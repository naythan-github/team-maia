#!/usr/bin/env python3
"""
Self-Consistency: Generate multiple responses and select most common conclusion

This advanced prompting technique improves reliability by:
1. Generating N responses to the same prompt (N=3-5)
2. Parsing conclusions from each response
3. Using majority voting to select most common conclusion
4. Filtering out noise and inconsistencies

Use cases:
- Questions with ambiguous requirements
- Tasks with multiple valid interpretations
- Scenarios where confidence matters
- Problems requiring consensus validation

Reference: "Self-Consistency Improves Chain of Thought Reasoning in Language Models"
           Wang et al., 2022 (ICLR 2023)
"""

import json
import re
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Callable, Any
from collections import Counter
from datetime import datetime
from pathlib import Path
from enum import Enum

class ConsistencyLevel(Enum):
    """Consistency strength"""
    UNANIMOUS = "unanimous"  # 100% agreement
    STRONG = "strong"        # 80%+ agreement
    MODERATE = "moderate"    # 60-79% agreement
    WEAK = "weak"            # 40-59% agreement
    NO_CONSENSUS = "no_consensus"  # <40% agreement

@dataclass
class Response:
    """Single generated response"""
    id: str
    content: str
    conclusion: Optional[str] = None
    reasoning_path: List[str] = field(default_factory=list)
    confidence: Optional[float] = None
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

@dataclass
class ConsensusResult:
    """Result of self-consistency analysis"""
    problem: str
    selected_conclusion: str
    consistency_level: ConsistencyLevel
    vote_counts: Dict[str, int]
    total_responses: int
    agreement_percentage: float
    all_responses: List[Response]
    reasoning_paths: List[List[str]]
    confidence_score: float
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

class SelfConsistencyEngine:
    """Engine for self-consistency reasoning"""

    def __init__(
        self,
        num_samples: int = 5,
        temperature: float = 0.7,
        conclusion_extractor: Optional[Callable] = None
    ):
        """
        Initialize self-consistency engine

        Args:
            num_samples: Number of responses to generate (3-5 recommended)
            temperature: Sampling temperature (higher = more diverse)
            conclusion_extractor: Custom function to extract conclusions from responses
        """
        self.num_samples = num_samples
        self.temperature = temperature
        self.conclusion_extractor = conclusion_extractor or self._default_conclusion_extractor

        # Storage
        self.results_dir = Path(__file__).parent.parent.parent / "data" / "self_consistency"
        self.results_dir.mkdir(parents=True, exist_ok=True)
        self.results_file = self.results_dir / "results.json"

    def solve(
        self,
        problem: str,
        context: Optional[Dict] = None,
        response_generator: Optional[Callable] = None
    ) -> ConsensusResult:
        """
        Apply self-consistency to a problem

        Process:
        1. Generate N responses to same problem
        2. Extract conclusion from each response
        3. Count votes for each conclusion
        4. Select most common conclusion
        5. Calculate consistency metrics

        Args:
            problem: Problem to solve
            context: Optional context for problem
            response_generator: Optional custom response generator

        Returns:
            ConsensusResult with selected conclusion and metrics
        """
        # Generate multiple responses
        responses = self._generate_responses(problem, context, response_generator)

        # Extract conclusions from each response
        for response in responses:
            response.conclusion = self.conclusion_extractor(response.content)
            response.reasoning_path = self._extract_reasoning_path(response.content)

        # Count votes for each conclusion
        conclusions = [r.conclusion for r in responses if r.conclusion]
        if not conclusions:
            raise ValueError("No valid conclusions extracted from responses")

        vote_counts = dict(Counter(conclusions))
        total_votes = len(conclusions)

        # Select most common conclusion
        selected_conclusion = max(vote_counts.items(), key=lambda x: x[1])[0]
        agreement_percentage = (vote_counts[selected_conclusion] / total_votes) * 100

        # Determine consistency level
        consistency_level = self._determine_consistency_level(agreement_percentage)

        # Calculate confidence score (weighted by agreement and response quality)
        confidence_score = self._calculate_confidence(responses, selected_conclusion)

        # Collect reasoning paths
        reasoning_paths = [r.reasoning_path for r in responses if r.conclusion == selected_conclusion]

        result = ConsensusResult(
            problem=problem,
            selected_conclusion=selected_conclusion,
            consistency_level=consistency_level,
            vote_counts=vote_counts,
            total_responses=total_votes,
            agreement_percentage=agreement_percentage,
            all_responses=responses,
            reasoning_paths=reasoning_paths,
            confidence_score=confidence_score
        )

        # Save result
        self._save_result(result)

        return result

    def _generate_responses(
        self,
        problem: str,
        context: Optional[Dict],
        response_generator: Optional[Callable]
    ) -> List[Response]:
        """Generate N responses to the problem"""
        responses = []

        for i in range(self.num_samples):
            if response_generator:
                content = response_generator(problem, context, temperature=self.temperature)
            else:
                # Simulate response generation (in production, call actual LLM)
                content = self._simulate_response(problem, context, i)

            response = Response(
                id=f"response_{i+1}",
                content=content
            )
            responses.append(response)

        return responses

    def _simulate_response(self, problem: str, context: Optional[Dict], seed: int) -> str:
        """
        Simulate response generation (for testing without LLM)

        In production, this would call actual LLM API
        """
        # Mock responses for demonstration
        if "architecture" in problem.lower():
            mock_conclusions = [
                "Use microservices with API gateway for scalability",
                "Use microservices with API gateway for scalability",
                "Use microservices with event-driven messaging",
                "Use modular monolith with service boundaries",
                "Use microservices with API gateway for scalability"
            ]
            mock_reasoning = [
                [
                    "Analyze requirements: High traffic, need independent scaling",
                    "Consider options: Monolith vs Microservices vs Serverless",
                    "Select microservices for independent scaling",
                    "Add API gateway for unified entry point"
                ],
                [
                    "Identify scalability needs: 1M+ users",
                    "Evaluate architectures: Microservices provide best isolation",
                    "Choose API gateway pattern for routing and security",
                    "Conclude: Microservices + API gateway"
                ],
                [
                    "Problem: Need to scale components independently",
                    "Solution space: Service-oriented architectures",
                    "Event-driven messaging provides loose coupling",
                    "Select microservices with async communication"
                ],
                [
                    "Start with monolith for simplicity",
                    "Use service boundaries to prepare for future split",
                    "Modular monolith allows gradual evolution",
                    "Avoid premature microservices complexity"
                ],
                [
                    "High availability requirement",
                    "Microservices enable fault isolation",
                    "API gateway provides circuit breaking",
                    "Best fit: Microservices + API gateway"
                ]
            ]
        elif "database" in problem.lower():
            mock_conclusions = [
                "Use PostgreSQL with read replicas",
                "Use PostgreSQL with read replicas",
                "Use PostgreSQL with read replicas",
                "Use PostgreSQL with connection pooling",
                "Use PostgreSQL with read replicas"
            ]
            mock_reasoning = [
                ["Analyze data model: Relational", "Consider read-heavy workload", "Add read replicas for scalability"],
                ["Structured data needs ACID", "PostgreSQL provides reliability", "Scale reads with replicas"],
                ["Data consistency critical", "Use PostgreSQL for transactions", "Distribute reads across replicas"],
                ["High connection count", "Connection pooling reduces overhead", "PostgreSQL with PgBouncer"],
                ["Read/write ratio 80/20", "PostgreSQL primary + replicas", "Route reads to replicas"]
            ]
        else:
            # Generic fallback
            mock_conclusions = [
                "Option A is optimal",
                "Option A is optimal",
                "Option B provides better long-term value",
                "Option A is optimal",
                "Option A is optimal"
            ]
            mock_reasoning = [
                ["Analyze options", "Compare trade-offs", "Select Option A"],
                ["Evaluate criteria", "Option A wins on performance", "Choose A"],
                ["Long-term sustainability matters", "Option B more maintainable", "Select B"],
                ["Performance critical", "Option A faster", "Choose A"],
                ["Cost-benefit analysis", "Option A best ROI", "Select A"]
            ]

        conclusion = mock_conclusions[seed % len(mock_conclusions)]
        reasoning = mock_reasoning[seed % len(mock_reasoning)]

        # Format as response with reasoning
        response = f"**Problem Analysis**: {problem}\n\n"
        response += "**Reasoning**:\n"
        for i, step in enumerate(reasoning, 1):
            response += f"{i}. {step}\n"
        response += f"\n**Conclusion**: {conclusion}\n"

        return response

    def _default_conclusion_extractor(self, response_content: str) -> Optional[str]:
        """
        Default conclusion extractor using regex patterns

        Looks for patterns like:
        - "Conclusion: X"
        - "Therefore, X"
        - "In conclusion, X"
        - Final sentence if no explicit conclusion marker
        """
        # Try explicit conclusion markers
        patterns = [
            r"\*\*Conclusion\*\*:\s*(.+?)(?:\n|$)",
            r"Conclusion:\s*(.+?)(?:\n|$)",
            r"Therefore,\s*(.+?)(?:\n|$)",
            r"In conclusion,\s*(.+?)(?:\n|$)",
            r"Final recommendation:\s*(.+?)(?:\n|$)",
            r"Selected approach:\s*(.+?)(?:\n|$)"
        ]

        for pattern in patterns:
            match = re.search(pattern, response_content, re.IGNORECASE)
            if match:
                return match.group(1).strip()

        # Fallback: Use last sentence
        sentences = response_content.split('.')
        if sentences:
            return sentences[-1].strip()

        return None

    def _extract_reasoning_path(self, response_content: str) -> List[str]:
        """Extract reasoning steps from response"""
        # Look for numbered or bulleted lists
        steps = []

        # Try numbered format (1. X, 2. Y, 3. Z)
        numbered_pattern = r"^\d+\.\s*(.+?)$"
        for line in response_content.split('\n'):
            match = re.match(numbered_pattern, line.strip())
            if match:
                steps.append(match.group(1))

        if steps:
            return steps

        # Try bullet format (- X, - Y, - Z)
        bullet_pattern = r"^[-*]\s*(.+?)$"
        for line in response_content.split('\n'):
            match = re.match(bullet_pattern, line.strip())
            if match:
                steps.append(match.group(1))

        return steps

    def _determine_consistency_level(self, agreement_percentage: float) -> ConsistencyLevel:
        """Determine consistency level from agreement percentage"""
        if agreement_percentage == 100:
            return ConsistencyLevel.UNANIMOUS
        elif agreement_percentage >= 80:
            return ConsistencyLevel.STRONG
        elif agreement_percentage >= 60:
            return ConsistencyLevel.MODERATE
        elif agreement_percentage >= 40:
            return ConsistencyLevel.WEAK
        else:
            return ConsistencyLevel.NO_CONSENSUS

    def _calculate_confidence(self, responses: List[Response], selected_conclusion: str) -> float:
        """
        Calculate confidence score

        Factors:
        - Agreement percentage (primary weight)
        - Response quality (reasoning depth)
        - Consistency of reasoning paths
        """
        # Agreement component (0-1)
        supporting_responses = [r for r in responses if r.conclusion == selected_conclusion]
        agreement_score = len(supporting_responses) / len(responses)

        # Reasoning quality component (0-1)
        avg_reasoning_depth = sum(len(r.reasoning_path) for r in supporting_responses) / max(len(supporting_responses), 1)
        quality_score = min(avg_reasoning_depth / 5.0, 1.0)  # Normalize to 0-1 (5 steps = perfect)

        # Weighted confidence (agreement 70%, quality 30%)
        confidence = (agreement_score * 0.7) + (quality_score * 0.3)

        return round(confidence, 3)

    def _save_result(self, result: ConsensusResult):
        """Save result to persistent storage"""
        # Load existing results
        results = []
        if self.results_file.exists():
            with open(self.results_file, 'r') as f:
                results = json.load(f)

        # Add new result (simplified for JSON)
        result_dict = {
            'problem': result.problem,
            'selected_conclusion': result.selected_conclusion,
            'consistency_level': result.consistency_level.value,
            'vote_counts': result.vote_counts,
            'total_responses': result.total_responses,
            'agreement_percentage': result.agreement_percentage,
            'confidence_score': result.confidence_score,
            'timestamp': result.timestamp,
            'response_ids': [r.id for r in result.all_responses]
        }
        results.append(result_dict)

        # Save
        with open(self.results_file, 'w') as f:
            json.dump(results, f, indent=2)

    def compare_to_single_response(
        self,
        problem: str,
        single_response: str,
        consensus_result: ConsensusResult
    ) -> Dict[str, Any]:
        """
        Compare self-consistency result to single response

        Returns metrics showing improvement
        """
        single_conclusion = self.conclusion_extractor(single_response)

        return {
            'problem': problem,
            'single_response_conclusion': single_conclusion,
            'consensus_conclusion': consensus_result.selected_conclusion,
            'agreement_percentage': consensus_result.agreement_percentage,
            'consistency_level': consensus_result.consistency_level.value,
            'confidence_score': consensus_result.confidence_score,
            'conclusions_match': single_conclusion == consensus_result.selected_conclusion,
            'reasoning_paths_explored': len(consensus_result.reasoning_paths),
            'vote_distribution': consensus_result.vote_counts
        }

def demo():
    """Demonstrate self-consistency engine"""
    print("=" * 80)
    print("Self-Consistency Engine Demo")
    print("=" * 80)

    engine = SelfConsistencyEngine(num_samples=5, temperature=0.7)

    # Test Case 1: Architecture design question
    print("\n📋 Test Case 1: Architecture Design Question")
    print("-" * 80)
    problem1 = "Design a scalable architecture for e-commerce platform with 1M+ users"

    result1 = engine.solve(problem1)

    print(f"Problem: {result1.problem}")
    print(f"\n✅ Selected Conclusion (by majority vote):")
    print(f"   {result1.selected_conclusion}")
    print(f"\n📊 Consistency Metrics:")
    print(f"   - Agreement: {result1.agreement_percentage:.1f}%")
    print(f"   - Consistency Level: {result1.consistency_level.value.upper()}")
    print(f"   - Confidence Score: {result1.confidence_score:.3f}")
    print(f"   - Total Responses: {result1.total_responses}")
    print(f"\n🗳️  Vote Distribution:")
    for conclusion, count in sorted(result1.vote_counts.items(), key=lambda x: x[1], reverse=True):
        percentage = (count / result1.total_responses) * 100
        print(f"   - {conclusion}: {count} votes ({percentage:.1f}%)")

    print(f"\n🧠 Reasoning Paths (from supporting responses):")
    for i, path in enumerate(result1.reasoning_paths[:2], 1):  # Show first 2
        print(f"   Path {i}:")
        for step in path:
            print(f"      → {step}")

    # Test Case 2: Database selection question
    print("\n" + "=" * 80)
    print("📋 Test Case 2: Database Selection Question")
    print("-" * 80)
    problem2 = "Choose optimal database for high-read workload with 80/20 read/write ratio"

    result2 = engine.solve(problem2)

    print(f"Problem: {result2.problem}")
    print(f"\n✅ Selected Conclusion:")
    print(f"   {result2.selected_conclusion}")
    print(f"\n📊 Consistency Metrics:")
    print(f"   - Agreement: {result2.agreement_percentage:.1f}%")
    print(f"   - Consistency Level: {result2.consistency_level.value.upper()}")
    print(f"   - Confidence Score: {result2.confidence_score:.3f}")
    print(f"\n🗳️  Vote Distribution:")
    for conclusion, count in sorted(result2.vote_counts.items(), key=lambda x: x[1], reverse=True):
        percentage = (count / result2.total_responses) * 100
        print(f"   - {conclusion}: {count} votes ({percentage:.1f}%)")

    # Comparison with single response
    print("\n" + "=" * 80)
    print("📊 Self-Consistency vs Single Response Comparison")
    print("-" * 80)

    single_response = engine._simulate_response(problem1, None, 0)
    comparison = engine.compare_to_single_response(problem1, single_response, result1)

    print(f"Problem: {problem1}\n")
    print(f"Single Response Conclusion:")
    print(f"   {comparison['single_response_conclusion']}")
    print(f"\nSelf-Consistency Conclusion:")
    print(f"   {comparison['consensus_conclusion']}")
    print(f"\n✅ Conclusions Match: {comparison['conclusions_match']}")
    print(f"\n📈 Self-Consistency Benefits:")
    print(f"   - Reasoning Paths Explored: {comparison['reasoning_paths_explored']}")
    print(f"   - Agreement Level: {comparison['agreement_percentage']:.1f}%")
    print(f"   - Confidence Score: {comparison['confidence_score']:.3f}")
    print(f"   - Consistency Level: {comparison['consistency_level'].upper()}")

    print("\n" + "=" * 80)
    print("✅ Demo Complete")
    print("=" * 80)
    print(f"\nResults saved to: {engine.results_file}")

if __name__ == "__main__":
    demo()
