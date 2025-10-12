"""
Automated Quality Scorer - Rubric-Based Response Evaluation

Evaluates agent responses using a comprehensive quality rubric covering:
- Task completion (40%)
- Tool calling accuracy (20%)
- Problem decomposition (20%)
- Response quality (15%)
- Efficiency (5%)

Based on: claude/data/AGENT_EVOLUTION_PROJECT_PLAN.md Phase 4, Task 4.2
Research: claude/data/PROMPT_ENGINEER_AGENT_ANALYSIS.md Section 5
"""

import json
from pathlib import Path
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional
from datetime import datetime
from enum import Enum


class CriteriaScore(Enum):
    """Standardized scoring levels"""
    EXCELLENT = 1.0      # 100% - Exceeds expectations
    GOOD = 0.85          # 85% - Meets all expectations
    SATISFACTORY = 0.7   # 70% - Meets most expectations
    NEEDS_IMPROVEMENT = 0.5  # 50% - Partially meets expectations
    POOR = 0.25          # 25% - Does not meet expectations


@dataclass
class CriteriaEvaluation:
    """Evaluation of a single criteria"""
    name: str
    score: float  # 0.0 to 1.0
    weight: float  # Percentage (e.g., 0.4 for 40%)
    feedback: str
    evidence: List[str] = field(default_factory=list)


@dataclass
class QualityScore:
    """Complete quality evaluation"""
    overall_score: float  # 0-100
    task_completion_score: float
    tool_accuracy_score: float
    decomposition_score: float
    response_quality_score: float
    efficiency_score: float
    criteria_evaluations: List[CriteriaEvaluation]
    timestamp: datetime
    agent_name: str
    response_id: str


class QualityRubric:
    """
    Comprehensive quality rubric for agent response evaluation.

    Based on research-validated criteria:
    - Task Completion (40%): Did the agent fully complete the task?
    - Tool Calling Accuracy (20%): Were tools used correctly?
    - Problem Decomposition (20%): Was the approach systematic?
    - Response Quality (15%): Was communication clear and helpful?
    - Efficiency (5%): Was the solution efficient?
    """

    def __init__(self):
        self.weights = {
            "task_completion": 0.40,
            "tool_accuracy": 0.20,
            "decomposition": 0.20,
            "response_quality": 0.15,
            "efficiency": 0.05
        }

    def evaluate_task_completion(self, response_data: Dict[str, Any]) -> CriteriaEvaluation:
        """
        Evaluate task completion (40% weight).

        Criteria:
        - All requirements addressed
        - Task fully resolved (not partial)
        - Edge cases considered
        - Validation performed
        """
        score = 0.0
        evidence = []

        # Check if task marked as completed
        if response_data.get("status") == "completed":
            score += 0.4
            evidence.append("Task marked as completed")
        elif response_data.get("status") == "partial":
            score += 0.2
            evidence.append("Task partially completed")

        # Check if all requirements addressed
        requirements = response_data.get("requirements", [])
        addressed = response_data.get("addressed_requirements", [])
        if requirements and addressed:
            completion_rate = len(addressed) / len(requirements)
            score += 0.3 * completion_rate
            evidence.append(f"Requirements: {len(addressed)}/{len(requirements)} addressed")
        elif not requirements:
            # If no explicit requirements, assume addressed
            score += 0.3
            evidence.append("No explicit requirements specified")

        # Check for validation
        if response_data.get("validation_performed"):
            score += 0.15
            evidence.append("Validation performed")

        # Check for edge case consideration
        if response_data.get("edge_cases_considered"):
            score += 0.15
            evidence.append("Edge cases considered")

        # Normalize to 0-1 range
        score = min(score, 1.0)

        # Determine feedback
        if score >= 0.9:
            feedback = "Excellent task completion - all requirements met with validation"
        elif score >= 0.7:
            feedback = "Good task completion - most requirements met"
        elif score >= 0.5:
            feedback = "Satisfactory - task completed but missing some requirements"
        else:
            feedback = "Needs improvement - task incomplete or many requirements unaddressed"

        return CriteriaEvaluation(
            name="task_completion",
            score=score,
            weight=self.weights["task_completion"],
            feedback=feedback,
            evidence=evidence
        )

    def evaluate_tool_accuracy(self, response_data: Dict[str, Any]) -> CriteriaEvaluation:
        """
        Evaluate tool calling accuracy (20% weight).

        Criteria:
        - Correct tools selected
        - Appropriate parameters
        - No redundant calls
        - Tools used efficiently
        """
        score = 0.0
        evidence = []

        tool_calls = response_data.get("tool_calls", [])

        if not tool_calls:
            # No tools needed or used
            if response_data.get("tools_required") == False:
                score = 1.0
                evidence.append("No tools required for this task")
            else:
                score = 0.5
                evidence.append("No tools used (may be incomplete)")
        else:
            # Evaluate tool usage
            correct_calls = response_data.get("correct_tool_calls", 0)
            total_calls = len(tool_calls)

            # Correctness
            if total_calls > 0:
                correctness_rate = correct_calls / total_calls
                score += 0.5 * correctness_rate
                evidence.append(f"Tool correctness: {correct_calls}/{total_calls}")

            # Parameter appropriateness
            if response_data.get("parameters_appropriate"):
                score += 0.25
                evidence.append("Parameters appropriate")

            # No redundant calls
            redundant = response_data.get("redundant_calls", 0)
            if redundant == 0:
                score += 0.25
                evidence.append("No redundant tool calls")
            else:
                evidence.append(f"{redundant} redundant tool calls")

        score = min(score, 1.0)

        if score >= 0.9:
            feedback = "Excellent tool usage - correct selections with optimal parameters"
        elif score >= 0.7:
            feedback = "Good tool usage - mostly correct with minor issues"
        elif score >= 0.5:
            feedback = "Satisfactory - tools used but with some errors"
        else:
            feedback = "Needs improvement - incorrect tool selections or parameters"

        return CriteriaEvaluation(
            name="tool_accuracy",
            score=score,
            weight=self.weights["tool_accuracy"],
            feedback=feedback,
            evidence=evidence
        )

    def evaluate_decomposition(self, response_data: Dict[str, Any]) -> CriteriaEvaluation:
        """
        Evaluate problem decomposition (20% weight).

        Criteria:
        - Clear understanding demonstrated
        - Systematic planning
        - Logical breakdown
        - Edge cases identified
        """
        score = 0.0
        evidence = []

        # Check for explicit planning
        if response_data.get("planning_shown"):
            score += 0.3
            evidence.append("Explicit planning demonstrated")

        # Check for systematic approach
        if response_data.get("systematic_approach"):
            score += 0.3
            evidence.append("Systematic approach used")

        # Check for logical breakdown
        subtasks = response_data.get("subtasks", [])
        if len(subtasks) > 1:
            score += 0.2
            evidence.append(f"Task broken into {len(subtasks)} subtasks")

        # Check for edge case identification
        edge_cases = response_data.get("edge_cases_identified", [])
        if edge_cases:
            score += 0.2
            evidence.append(f"{len(edge_cases)} edge cases identified")

        score = min(score, 1.0)

        if score >= 0.8:
            feedback = "Excellent decomposition - systematic and thorough"
        elif score >= 0.6:
            feedback = "Good decomposition - clear approach"
        elif score >= 0.4:
            feedback = "Satisfactory - basic decomposition present"
        else:
            feedback = "Needs improvement - ad-hoc approach"

        return CriteriaEvaluation(
            name="decomposition",
            score=score,
            weight=self.weights["decomposition"],
            feedback=feedback,
            evidence=evidence
        )

    def evaluate_response_quality(self, response_data: Dict[str, Any]) -> CriteriaEvaluation:
        """
        Evaluate response quality (15% weight).

        Criteria:
        - Clear communication
        - Helpful explanations
        - Appropriate detail level
        - Professional tone
        """
        score = 0.0
        evidence = []

        response_text = response_data.get("response_text", "")

        # Check clarity (not too verbose, not too terse)
        word_count = len(response_text.split())
        if 50 <= word_count <= 500:
            score += 0.3
            evidence.append(f"Appropriate length ({word_count} words)")
        elif word_count < 50:
            evidence.append("Response too brief")
        else:
            evidence.append("Response too verbose")

        # Check for explanations
        if response_data.get("explanations_provided"):
            score += 0.3
            evidence.append("Explanations provided")

        # Check for examples
        if response_data.get("examples_included"):
            score += 0.2
            evidence.append("Examples included")

        # Check tone (heuristic based on response data)
        if response_data.get("professional_tone"):
            score += 0.2
            evidence.append("Professional tone")

        score = min(score, 1.0)

        if score >= 0.8:
            feedback = "Excellent communication - clear, helpful, and professional"
        elif score >= 0.6:
            feedback = "Good communication - clear and helpful"
        elif score >= 0.4:
            feedback = "Satisfactory - adequate communication"
        else:
            feedback = "Needs improvement - unclear or unhelpful"

        return CriteriaEvaluation(
            name="response_quality",
            score=score,
            weight=self.weights["response_quality"],
            feedback=feedback,
            evidence=evidence
        )

    def evaluate_efficiency(self, response_data: Dict[str, Any]) -> CriteriaEvaluation:
        """
        Evaluate efficiency (5% weight).

        Criteria:
        - Minimal redundancy
        - Optimal tool usage
        - Token efficiency
        - Time to completion
        """
        score = 0.0
        evidence = []

        # Check token usage
        tokens_used = response_data.get("tokens_used", 0)
        tokens_expected = response_data.get("tokens_expected", tokens_used)
        if tokens_expected > 0:
            efficiency_ratio = min(tokens_expected / tokens_used, 1.0)
            score += 0.4 * efficiency_ratio
            evidence.append(f"Token efficiency: {tokens_used}/{tokens_expected}")

        # Check execution time
        execution_time = response_data.get("execution_time_ms", 0)
        if execution_time < 5000:  # Under 5 seconds
            score += 0.3
            evidence.append(f"Fast execution ({execution_time}ms)")
        elif execution_time < 10000:  # Under 10 seconds
            score += 0.15
            evidence.append(f"Moderate execution ({execution_time}ms)")

        # Check for redundancy
        if not response_data.get("redundant_operations"):
            score += 0.3
            evidence.append("No redundant operations")

        score = min(score, 1.0)

        if score >= 0.8:
            feedback = "Excellent efficiency - optimal resource usage"
        elif score >= 0.6:
            feedback = "Good efficiency - reasonable resource usage"
        elif score >= 0.4:
            feedback = "Satisfactory - acceptable efficiency"
        else:
            feedback = "Needs improvement - inefficient resource usage"

        return CriteriaEvaluation(
            name="efficiency",
            score=score,
            weight=self.weights["efficiency"],
            feedback=feedback,
            evidence=evidence
        )


class AutomatedQualityScorer:
    """
    Main quality scoring system for automated agent evaluation.

    Usage:
        scorer = AutomatedQualityScorer()

        response_data = {
            "status": "completed",
            "requirements": ["req1", "req2"],
            "addressed_requirements": ["req1", "req2"],
            "tool_calls": [...],
            "response_text": "...",
            ...
        }

        score = scorer.evaluate_response(response_data, "agent_name", "response_id")
        print(f"Overall Score: {score.overall_score}/100")
    """

    def __init__(self, score_dir: Path = None):
        self.rubric = QualityRubric()

        if score_dir is None:
            score_dir = Path(__file__).parent.parent.parent / "context" / "session" / "quality_scores"
        self.score_dir = score_dir
        self.score_dir.mkdir(parents=True, exist_ok=True)

    def evaluate_response(self, response_data: Dict[str, Any],
                         agent_name: str, response_id: str) -> QualityScore:
        """
        Evaluate a complete agent response.

        Args:
            response_data: Dict containing response metadata and content
            agent_name: Name of the agent that generated the response
            response_id: Unique identifier for this response

        Returns:
            QualityScore with overall score (0-100) and detailed breakdown
        """
        # Evaluate each criteria
        task_completion = self.rubric.evaluate_task_completion(response_data)
        tool_accuracy = self.rubric.evaluate_tool_accuracy(response_data)
        decomposition = self.rubric.evaluate_decomposition(response_data)
        response_quality = self.rubric.evaluate_response_quality(response_data)
        efficiency = self.rubric.evaluate_efficiency(response_data)

        # Calculate weighted overall score
        overall = (
            task_completion.score * task_completion.weight +
            tool_accuracy.score * tool_accuracy.weight +
            decomposition.score * decomposition.weight +
            response_quality.score * response_quality.weight +
            efficiency.score * efficiency.weight
        ) * 100  # Convert to 0-100 scale

        # Create quality score object
        quality_score = QualityScore(
            overall_score=overall,
            task_completion_score=task_completion.score * 100,
            tool_accuracy_score=tool_accuracy.score * 100,
            decomposition_score=decomposition.score * 100,
            response_quality_score=response_quality.score * 100,
            efficiency_score=efficiency.score * 100,
            criteria_evaluations=[
                task_completion,
                tool_accuracy,
                decomposition,
                response_quality,
                efficiency
            ],
            timestamp=datetime.now(),
            agent_name=agent_name,
            response_id=response_id
        )

        # Save score
        self._save_score(quality_score)

        return quality_score

    def _save_score(self, score: QualityScore):
        """Save quality score to disk"""
        score_file = self.score_dir / f"{score.response_id}.json"

        score_data = {
            "overall_score": score.overall_score,
            "task_completion_score": score.task_completion_score,
            "tool_accuracy_score": score.tool_accuracy_score,
            "decomposition_score": score.decomposition_score,
            "response_quality_score": score.response_quality_score,
            "efficiency_score": score.efficiency_score,
            "agent_name": score.agent_name,
            "response_id": score.response_id,
            "timestamp": score.timestamp.isoformat(),
            "criteria_evaluations": [
                {
                    "name": ce.name,
                    "score": ce.score,
                    "weight": ce.weight,
                    "feedback": ce.feedback,
                    "evidence": ce.evidence
                }
                for ce in score.criteria_evaluations
            ]
        }

        score_file.write_text(json.dumps(score_data, indent=2))

    def get_agent_scores(self, agent_name: str, limit: int = 100) -> List[QualityScore]:
        """
        Retrieve recent scores for a specific agent.

        Args:
            agent_name: Name of agent
            limit: Maximum number of scores to return

        Returns:
            List of QualityScore objects, most recent first
        """
        scores = []

        for score_file in sorted(self.score_dir.glob("*.json"), reverse=True):
            if len(scores) >= limit:
                break

            try:
                data = json.loads(score_file.read_text())
                if data.get("agent_name") == agent_name:
                    # Reconstruct QualityScore (simplified - just need overall)
                    scores.append(data)
            except (json.JSONDecodeError, KeyError):
                continue

        return scores

    def get_average_score(self, agent_name: str, days: int = 7) -> float:
        """
        Calculate average quality score for an agent over time period.

        Args:
            agent_name: Name of agent
            days: Number of days to look back

        Returns:
            Average score (0-100) or 0 if no scores
        """
        from datetime import timedelta

        cutoff = datetime.now() - timedelta(days=days)
        scores = []

        for score_file in self.score_dir.glob("*.json"):
            try:
                data = json.loads(score_file.read_text())
                if data.get("agent_name") == agent_name:
                    timestamp = datetime.fromisoformat(data["timestamp"])
                    if timestamp >= cutoff:
                        scores.append(data["overall_score"])
            except (json.JSONDecodeError, KeyError, ValueError):
                continue

        return sum(scores) / len(scores) if scores else 0.0


def main():
    """CLI entry point for manual scoring"""
    import argparse

    parser = argparse.ArgumentParser(description="Automated Quality Scorer")
    parser.add_argument("--agent", required=True, help="Agent name")
    parser.add_argument("--response-id", required=True, help="Response ID")
    parser.add_argument("--status", default="completed", help="Response status")

    args = parser.parse_args()

    # Example response data (would come from real execution)
    response_data = {
        "status": args.status,
        "requirements": ["req1", "req2"],
        "addressed_requirements": ["req1", "req2"],
        "validation_performed": True,
        "tool_calls": [],
        "tools_required": False,
        "planning_shown": True,
        "systematic_approach": True,
        "response_text": "This is a test response with appropriate detail level.",
        "explanations_provided": True,
        "professional_tone": True,
        "tokens_used": 500,
        "execution_time_ms": 2000
    }

    scorer = AutomatedQualityScorer()
    score = scorer.evaluate_response(response_data, args.agent, args.response_id)

    print(f"\n{'='*60}")
    print(f"Quality Score Report")
    print(f"{'='*60}")
    print(f"Agent: {score.agent_name}")
    print(f"Response ID: {score.response_id}")
    print(f"\nOverall Score: {score.overall_score:.1f}/100")
    print(f"\nBreakdown:")
    print(f"  Task Completion: {score.task_completion_score:.1f}/100 (40% weight)")
    print(f"  Tool Accuracy: {score.tool_accuracy_score:.1f}/100 (20% weight)")
    print(f"  Decomposition: {score.decomposition_score:.1f}/100 (20% weight)")
    print(f"  Response Quality: {score.response_quality_score:.1f}/100 (15% weight)")
    print(f"  Efficiency: {score.efficiency_score:.1f}/100 (5% weight)")
    print(f"\nDetailed Feedback:")
    for criteria in score.criteria_evaluations:
        print(f"\n{criteria.name.replace('_', ' ').title()}:")
        print(f"  {criteria.feedback}")
        for evidence in criteria.evidence:
            print(f"    • {evidence}")


if __name__ == "__main__":
    main()
