#!/usr/bin/env python3
"""
Agent A/B Testing Framework for Maia
=====================================

Purpose: Measure agent prompt improvement impact through controlled experiments

Features:
- A/B test agent variations (baseline vs improved)
- Quality rubric scoring (0-100 scale)
- Statistical significance testing (two-proportion Z-test)
- Test scenario library management
- Automated comparison reports

Usage:
    python agent_ab_testing_framework.py --agent dns_specialist --scenarios 20

Source: claude/data/PROMPT_ENGINEER_AGENT_ANALYSIS.md Section 5
"""

import json
import statistics
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Tuple
import math


@dataclass
class TestScenario:
    """A single test scenario for agent evaluation"""
    id: str
    description: str
    user_prompt: str
    expected_outcomes: List[str]
    difficulty: str  # "simple", "medium", "complex"
    domain: str  # e.g., "dns", "sre", "azure"

    def to_dict(self):
        return asdict(self)


@dataclass
class AgentResponse:
    """Agent's response to a test scenario"""
    scenario_id: str
    agent_version: str  # "baseline" or "improved"
    response_text: str
    tools_used: List[str]
    execution_time_ms: int
    timestamp: str

    # Quality assessment (manual or automated)
    task_fully_resolved: bool = False
    task_partially_resolved: bool = False
    validation_performed: bool = False
    all_requirements_met: bool = False
    used_tools_correctly: bool = False
    used_tools_with_errors: bool = False
    no_hallucinated_tools: bool = False
    showed_planning: bool = False
    systematic_approach: bool = False
    considered_edge_cases: bool = False
    clear_communication: bool = False
    actionable_recommendations: bool = False
    appropriate_detail_level: bool = False
    continued_until_resolved: bool = False
    proactive_problem_solving: bool = False

    def to_dict(self):
        return asdict(self)


@dataclass
class QualityScore:
    """Quality rubric score breakdown (0-100 scale)"""
    task_completion: int  # 0-40 points
    tool_calling: int  # 0-20 points
    problem_decomposition: int  # 0-20 points
    response_quality: int  # 0-15 points
    persistence: int  # 0-5 points
    total: int  # 0-100 points
    grade: str  # A/B/C/D/F

    def to_dict(self):
        return asdict(self)


class QualityRubric:
    """Score agent responses using 0-100 quality rubric

    Source: PROMPT_ENGINEER_AGENT_ANALYSIS.md Section 5
    """

    def score(self, response: AgentResponse) -> QualityScore:
        """Calculate quality score from agent response assessment"""

        task_completion = self._score_task_completion(response)
        tool_calling = self._score_tool_calling(response)
        problem_decomposition = self._score_problem_decomposition(response)
        response_quality = self._score_response_quality(response)
        persistence = self._score_persistence(response)

        total = task_completion + tool_calling + problem_decomposition + response_quality + persistence
        grade = self._assign_grade(total)

        return QualityScore(
            task_completion=task_completion,
            tool_calling=tool_calling,
            problem_decomposition=problem_decomposition,
            response_quality=response_quality,
            persistence=persistence,
            total=total,
            grade=grade
        )

    def _score_task_completion(self, response: AgentResponse) -> int:
        """40 points for complete task resolution"""
        score = 0

        if response.task_fully_resolved:
            score += 30  # Task completed
        elif response.task_partially_resolved:
            score += 15  # Partial completion

        if response.validation_performed:
            score += 5  # Validated solution

        if response.all_requirements_met:
            score += 5  # All requirements addressed

        return min(score, 40)

    def _score_tool_calling(self, response: AgentResponse) -> int:
        """20 points for correct tool usage"""
        score = 0

        if response.used_tools_correctly:
            score += 15  # Tools used properly
        elif response.used_tools_with_errors:
            score += 7  # Some tool errors

        if response.no_hallucinated_tools:
            score += 5  # Didn't invent tools

        return min(score, 20)

    def _score_problem_decomposition(self, response: AgentResponse) -> int:
        """20 points for systematic thinking"""
        score = 0

        if response.showed_planning:
            score += 8  # Explicit planning

        if response.systematic_approach:
            score += 7  # Logical breakdown

        if response.considered_edge_cases:
            score += 5  # Thorough analysis

        return min(score, 20)

    def _score_response_quality(self, response: AgentResponse) -> int:
        """15 points for communication quality"""
        score = 0

        if response.clear_communication:
            score += 7  # Easy to understand

        if response.actionable_recommendations:
            score += 5  # User can act on it

        if response.appropriate_detail_level:
            score += 3  # Not too verbose/terse

        return min(score, 15)

    def _score_persistence(self, response: AgentResponse) -> int:
        """5 points for thoroughness"""
        score = 0

        if response.continued_until_resolved:
            score += 3  # Didn't stop prematurely

        if response.proactive_problem_solving:
            score += 2  # Anticipated issues

        return min(score, 5)

    def _assign_grade(self, score: int) -> str:
        """Convert score to letter grade"""
        if score >= 90:
            return "A"
        elif score >= 80:
            return "B"
        elif score >= 70:
            return "C"
        elif score >= 60:
            return "D"
        else:
            return "F"


@dataclass
class ABTestResult:
    """Results from A/B test comparing baseline vs improved agent"""
    agent_name: str
    test_date: str
    baseline_version: str
    improved_version: str
    num_scenarios: int

    # Baseline metrics
    baseline_avg_score: float
    baseline_completion_rate: float
    baseline_avg_time_ms: float
    baseline_scores: List[int]

    # Improved metrics
    improved_avg_score: float
    improved_completion_rate: float
    improved_avg_time_ms: float
    improved_scores: List[int]

    # Comparison
    score_improvement_pct: float
    completion_improvement_pct: float
    time_change_pct: float
    statistically_significant: bool
    p_value: float

    # Decision
    recommendation: str  # "deploy", "refine", "reject"
    rationale: str

    def to_dict(self):
        return asdict(self)


class ABTestFramework:
    """A/B testing framework for agent prompt improvements

    Workflow:
    1. Load test scenarios
    2. Run baseline agent (v1)
    3. Run improved agent (v2)
    4. Score both with quality rubric
    5. Statistical analysis (two-proportion Z-test)
    6. Generate recommendation
    """

    def __init__(self, data_dir: Path = Path("claude/data/ab_tests")):
        self.data_dir = data_dir
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.rubric = QualityRubric()

    def load_scenarios(self, agent_name: str) -> List[TestScenario]:
        """Load test scenarios for specific agent"""
        scenarios_file = self.data_dir / f"{agent_name}_scenarios.json"

        if not scenarios_file.exists():
            print(f"⚠️  No scenarios found for {agent_name}")
            print(f"   Create scenarios at: {scenarios_file}")
            return []

        with open(scenarios_file, 'r') as f:
            data = json.load(f)

        scenarios = [TestScenario(**s) for s in data['scenarios']]
        print(f"✅ Loaded {len(scenarios)} scenarios for {agent_name}")
        return scenarios

    def save_scenarios(self, agent_name: str, scenarios: List[TestScenario]):
        """Save test scenarios for specific agent"""
        scenarios_file = self.data_dir / f"{agent_name}_scenarios.json"

        data = {
            'agent_name': agent_name,
            'created': datetime.now().isoformat(),
            'scenarios': [s.to_dict() for s in scenarios]
        }

        with open(scenarios_file, 'w') as f:
            json.dump(data, f, indent=2)

        print(f"✅ Saved {len(scenarios)} scenarios to {scenarios_file}")

    def run_experiment(
        self,
        agent_name: str,
        baseline_responses: List[AgentResponse],
        improved_responses: List[AgentResponse],
        baseline_version: str = "v1",
        improved_version: str = "v2"
    ) -> ABTestResult:
        """Run A/B test comparing baseline vs improved agent responses"""

        if len(baseline_responses) != len(improved_responses):
            raise ValueError("Baseline and improved must have same number of responses")

        # Score all responses
        baseline_scores = [self.rubric.score(r) for r in baseline_responses]
        improved_scores = [self.rubric.score(r) for r in improved_responses]

        # Calculate metrics
        baseline_avg = statistics.mean([s.total for s in baseline_scores])
        improved_avg = statistics.mean([s.total for s in improved_scores])

        baseline_completion = sum(1 for r in baseline_responses if r.task_fully_resolved) / len(baseline_responses)
        improved_completion = sum(1 for r in improved_responses if r.task_fully_resolved) / len(improved_responses)

        baseline_time = statistics.mean([r.execution_time_ms for r in baseline_responses])
        improved_time = statistics.mean([r.execution_time_ms for r in improved_responses])

        # Calculate improvements
        score_improvement = ((improved_avg - baseline_avg) / baseline_avg) * 100
        completion_improvement = ((improved_completion - baseline_completion) / baseline_completion) * 100 if baseline_completion > 0 else 0
        time_change = ((improved_time - baseline_time) / baseline_time) * 100

        # Statistical significance (two-proportion Z-test for completion rate)
        p_value = self._two_proportion_z_test(
            baseline_completion,
            improved_completion,
            len(baseline_responses),
            len(improved_responses)
        )
        statistically_significant = p_value < 0.05

        # Generate recommendation
        recommendation, rationale = self._generate_recommendation(
            score_improvement,
            completion_improvement,
            statistically_significant,
            p_value
        )

        return ABTestResult(
            agent_name=agent_name,
            test_date=datetime.now().isoformat(),
            baseline_version=baseline_version,
            improved_version=improved_version,
            num_scenarios=len(baseline_responses),
            baseline_avg_score=baseline_avg,
            baseline_completion_rate=baseline_completion,
            baseline_avg_time_ms=baseline_time,
            baseline_scores=[s.total for s in baseline_scores],
            improved_avg_score=improved_avg,
            improved_completion_rate=improved_completion,
            improved_avg_time_ms=improved_time,
            improved_scores=[s.total for s in improved_scores],
            score_improvement_pct=score_improvement,
            completion_improvement_pct=completion_improvement,
            time_change_pct=time_change,
            statistically_significant=statistically_significant,
            p_value=p_value,
            recommendation=recommendation,
            rationale=rationale
        )

    def _two_proportion_z_test(self, p1: float, p2: float, n1: int, n2: int) -> float:
        """Calculate p-value for two-proportion Z-test

        H0: p1 = p2 (no difference in completion rates)
        H1: p1 ≠ p2 (difference exists)
        """
        # Pooled proportion
        p_pool = (p1 * n1 + p2 * n2) / (n1 + n2)

        # Standard error
        se = math.sqrt(p_pool * (1 - p_pool) * (1/n1 + 1/n2))

        # Z-score
        if se == 0:
            return 1.0  # No variance, no difference

        z = (p2 - p1) / se

        # Two-tailed p-value (approximate using normal distribution)
        # For more accuracy, use scipy.stats.norm.sf(abs(z)) * 2
        # This is a simplified approximation
        if abs(z) > 2.58:  # 99% confidence
            return 0.01
        elif abs(z) > 1.96:  # 95% confidence
            return 0.05
        elif abs(z) > 1.65:  # 90% confidence
            return 0.10
        else:
            return 0.20  # Not significant

    def _generate_recommendation(
        self,
        score_improvement: float,
        completion_improvement: float,
        significant: bool,
        p_value: float
    ) -> Tuple[str, str]:
        """Generate deployment recommendation based on test results

        Decision criteria:
        - >15% improvement + p<0.05: Deploy
        - 10-15% improvement: Refine and retest
        - <10% improvement: Reject, try different approach
        """
        if score_improvement > 15 and significant:
            return "deploy", f"Strong improvement (+{score_improvement:.1f}%) with statistical significance (p={p_value:.3f}). Ready for production."

        elif score_improvement > 10 and significant:
            return "refine", f"Moderate improvement (+{score_improvement:.1f}%) with significance (p={p_value:.3f}). Consider further refinement before deploying."

        elif score_improvement > 15 and not significant:
            return "refine", f"Strong improvement (+{score_improvement:.1f}%) but not statistically significant (p={p_value:.3f}). Increase sample size and retest."

        elif score_improvement > 5:
            return "reject", f"Minor improvement (+{score_improvement:.1f}%). Try a different optimization approach for stronger impact."

        elif score_improvement < 0:
            return "reject", f"Regression detected ({score_improvement:.1f}%). Improved version is worse than baseline. Abandon this approach."

        else:
            return "reject", f"Minimal improvement (+{score_improvement:.1f}%). Not worth deploying."

    def save_results(self, result: ABTestResult):
        """Save A/B test results to file"""
        results_file = self.data_dir / f"{result.agent_name}_ab_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

        with open(results_file, 'w') as f:
            json.dump(result.to_dict(), f, indent=2)

        print(f"✅ Saved results to {results_file}")

    def generate_report(self, result: ABTestResult) -> str:
        """Generate human-readable A/B test report"""

        report = f"""
{'='*80}
A/B TEST REPORT: {result.agent_name}
{'='*80}

Test Date: {result.test_date}
Comparison: {result.baseline_version} (baseline) vs {result.improved_version} (improved)
Sample Size: {result.num_scenarios} scenarios per variation

BASELINE PERFORMANCE ({result.baseline_version}):
  - Average Quality Score: {result.baseline_avg_score:.1f}/100
  - Task Completion Rate: {result.baseline_completion_rate*100:.1f}%
  - Average Execution Time: {result.baseline_avg_time_ms:.0f}ms

IMPROVED PERFORMANCE ({result.improved_version}):
  - Average Quality Score: {result.improved_avg_score:.1f}/100
  - Task Completion Rate: {result.improved_completion_rate*100:.1f}%
  - Average Execution Time: {result.improved_avg_time_ms:.0f}ms

IMPROVEMENT ANALYSIS:
  - Quality Score: {result.score_improvement_pct:+.1f}% {'✅' if result.score_improvement_pct > 0 else '❌'}
  - Completion Rate: {result.completion_improvement_pct:+.1f}% {'✅' if result.completion_improvement_pct > 0 else '❌'}
  - Execution Time: {result.time_change_pct:+.1f}% {'✅' if result.time_change_pct < 0 else '⚠️'}

STATISTICAL SIGNIFICANCE:
  - P-value: {result.p_value:.3f}
  - Significant: {'YES ✅' if result.statistically_significant else 'NO ❌'}
  - Confidence: {'95%+' if result.p_value < 0.05 else '90%' if result.p_value < 0.10 else '<90%'}

RECOMMENDATION: {result.recommendation.upper()}
{result.rationale}

{'='*80}
"""
        return report


# Test scenario library examples
def create_dns_specialist_scenarios() -> List[TestScenario]:
    """Example test scenarios for DNS Specialist agent"""
    return [
        TestScenario(
            id="dns_01",
            description="Simple SPF record check",
            user_prompt="Check if example.com has SPF record configured",
            expected_outcomes=[
                "Queries DNS TXT records",
                "Identifies SPF record",
                "Explains SPF policy"
            ],
            difficulty="simple",
            domain="dns"
        ),
        TestScenario(
            id="dns_02",
            description="Email deliverability crisis",
            user_prompt="URGENT: Our emails suddenly going to spam! Need immediate fix.",
            expected_outcomes=[
                "Checks SPF, DKIM, DMARC",
                "Identifies root cause",
                "Provides fix instructions",
                "No premature stopping"
            ],
            difficulty="complex",
            domain="dns"
        ),
        TestScenario(
            id="dns_03",
            description="DNS migration planning",
            user_prompt="We're migrating from GoDaddy to Route53. What's the safest approach?",
            expected_outcomes=[
                "Explains migration steps",
                "Warns about TTL timing",
                "Provides validation checklist",
                "Addresses rollback strategy"
            ],
            difficulty="medium",
            domain="dns"
        ),
    ]


def create_sre_scenarios() -> List[TestScenario]:
    """Example test scenarios for SRE Principal Engineer agent"""
    return [
        TestScenario(
            id="sre_01",
            description="Database latency spike",
            user_prompt="URGENT: Database P95 latency spiked from 50ms to 2000ms 5 minutes ago.",
            expected_outcomes=[
                "Immediate assessment",
                "Checks recent changes",
                "Implements rollback or mitigation",
                "Sets up monitoring"
            ],
            difficulty="complex",
            domain="sre"
        ),
        TestScenario(
            id="sre_02",
            description="Simple metrics query",
            user_prompt="What's our API P95 latency for the last hour?",
            expected_outcomes=[
                "Queries Prometheus",
                "Returns current latency",
                "Compares to SLO"
            ],
            difficulty="simple",
            domain="sre"
        ),
    ]


if __name__ == "__main__":
    # Example usage
    framework = ABTestFramework()

    # Create example scenarios for DNS Specialist
    dns_scenarios = create_dns_specialist_scenarios()
    framework.save_scenarios("dns_specialist", dns_scenarios)

    # Create example scenarios for SRE
    sre_scenarios = create_sre_scenarios()
    framework.save_scenarios("sre_principal_engineer", sre_scenarios)

    print("\n✅ A/B Testing Framework initialized")
    print(f"   Data directory: {framework.data_dir}")
    print(f"   Scenarios created: DNS Specialist ({len(dns_scenarios)}), SRE ({len(sre_scenarios)})")
    print("\n📝 Next steps:")
    print("   1. Run baseline agent (v1) on test scenarios")
    print("   2. Run improved agent (v2) on same scenarios")
    print("   3. Score responses using framework.rubric.score()")
    print("   4. Run framework.run_experiment() to compare")
    print("   5. Review recommendation and deploy if approved")
