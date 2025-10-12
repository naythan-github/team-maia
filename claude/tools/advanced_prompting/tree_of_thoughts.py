#!/usr/bin/env python3
"""
Tree of Thoughts (ToT) Implementation
Advanced reasoning through exploration of multiple solution paths

**Concept**:
Instead of following a single reasoning path, ToT explores multiple possible approaches
in parallel, evaluates each path's promise, and selects the best path forward.

**Use Cases**:
- Complex problem-solving with multiple valid approaches
- Strategic planning with uncertain outcomes
- Architecture decisions with trade-offs
- Debugging with multiple hypotheses

**Comparison to Standard Prompting**:
- Standard: Linear reasoning (thought → action → result)
- ReACT: Iterative reasoning (thought → action → observation → reflection)
- ToT: Branching reasoning (multiple thoughts → evaluate → best path → action)

**Source**: Advanced prompt engineering research (Google Gemini + OpenAI)
**Author**: Maia (Phase 5: Advanced Research)
**Created**: 2025-10-12
"""

from typing import List, Dict, Any, Tuple, Optional
from dataclasses import dataclass, field
from enum import Enum
import json
from pathlib import Path


class ThoughtQuality(Enum):
    """Quality assessment for a thought/approach"""
    EXCELLENT = 5  # Very promising, explore further
    GOOD = 4       # Promising, worth exploring
    FAIR = 3       # Acceptable, explore if others fail
    POOR = 2       # Unlikely to succeed
    DEAD_END = 1   # Will not succeed


@dataclass
class Thought:
    """A single reasoning path/approach"""
    id: str
    content: str  # The actual reasoning/approach
    quality: ThoughtQuality
    rationale: str  # Why this quality was assigned
    parent_id: Optional[str] = None  # For tracking tree structure
    depth: int = 0  # How deep in the tree (0 = root)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "id": self.id,
            "content": self.content,
            "quality": self.quality.name,
            "quality_score": self.quality.value,
            "rationale": self.rationale,
            "parent_id": self.parent_id,
            "depth": self.depth
        }


@dataclass
class TreeOfThoughtsResult:
    """Result of Tree of Thoughts exploration"""
    problem: str
    selected_path: List[Thought]
    all_thoughts: List[Thought]
    reasoning_summary: str
    final_recommendation: str


class TreeOfThoughtsEngine:
    """
    Engine for Tree of Thoughts reasoning

    Process:
    1. Generate multiple initial approaches (breadth-first)
    2. Evaluate quality of each approach
    3. Select best approach(es) to expand
    4. Repeat until solution found or max depth reached
    5. Return best path and recommendation
    """

    def __init__(self, max_depth: int = 3, max_branches: int = 3):
        """
        Initialize ToT engine

        Args:
            max_depth: Maximum depth to explore (default: 3)
            max_branches: Maximum branches to explore at each level (default: 3)
        """
        self.max_depth = max_depth
        self.max_branches = max_branches
        self.maia_root = Path(__file__).resolve().parents[3]
        self.session_dir = self.maia_root / "claude" / "context" / "session" / "tree_of_thoughts"
        self.session_dir.mkdir(parents=True, exist_ok=True)

    def solve(self, problem: str, context: Optional[Dict[str, Any]] = None) -> TreeOfThoughtsResult:
        """
        Solve problem using Tree of Thoughts

        Args:
            problem: Problem statement
            context: Optional context about the problem

        Returns:
            TreeOfThoughtsResult with selected path and recommendation
        """
        context = context or {}

        # Step 1: Generate initial thoughts (multiple approaches)
        initial_thoughts = self._generate_initial_thoughts(problem, context)

        # Step 2: Evaluate and expand best thoughts
        all_thoughts = initial_thoughts[:]
        current_depth = 0

        while current_depth < self.max_depth:
            # Get best thoughts at current depth
            best_thoughts = self._select_best_thoughts(
                [t for t in all_thoughts if t.depth == current_depth]
            )

            if not best_thoughts:
                break

            # Expand each best thought
            for thought in best_thoughts:
                expansions = self._expand_thought(thought, problem, context)
                all_thoughts.extend(expansions)

            current_depth += 1

        # Step 3: Select best complete path
        selected_path = self._select_best_path(all_thoughts)

        # Step 4: Generate final recommendation
        final_recommendation = self._generate_recommendation(selected_path, problem)
        reasoning_summary = self._generate_reasoning_summary(selected_path, all_thoughts)

        # Save results
        result = TreeOfThoughtsResult(
            problem=problem,
            selected_path=selected_path,
            all_thoughts=all_thoughts,
            reasoning_summary=reasoning_summary,
            final_recommendation=final_recommendation
        )

        self._save_result(result)

        return result

    def _generate_initial_thoughts(self, problem: str, context: Dict[str, Any]) -> List[Thought]:
        """
        Generate multiple initial approaches to the problem

        For demonstration, this uses template-based generation.
        In production, this would use LLM to generate diverse approaches.
        """
        # Example: Different approaches to a system design problem
        if "design" in problem.lower() or "architecture" in problem.lower():
            return [
                Thought(
                    id="t_0_1",
                    content="Approach 1: Monolithic design with vertical scaling",
                    quality=ThoughtQuality.FAIR,
                    rationale="Simple to implement but limited scalability",
                    depth=0
                ),
                Thought(
                    id="t_0_2",
                    content="Approach 2: Microservices with horizontal scaling",
                    quality=ThoughtQuality.EXCELLENT,
                    rationale="Best scalability and flexibility, industry standard",
                    depth=0
                ),
                Thought(
                    id="t_0_3",
                    content="Approach 3: Serverless event-driven architecture",
                    quality=ThoughtQuality.GOOD,
                    rationale="Excellent cost efficiency, good for variable load",
                    depth=0
                )
            ]

        # Example: Debugging approaches
        elif "debug" in problem.lower() or "fix" in problem.lower():
            return [
                Thought(
                    id="t_0_1",
                    content="Approach 1: Check recent code changes (git diff)",
                    quality=ThoughtQuality.EXCELLENT,
                    rationale="Most issues caused by recent changes",
                    depth=0
                ),
                Thought(
                    id="t_0_2",
                    content="Approach 2: Analyze logs for error patterns",
                    quality=ThoughtQuality.GOOD,
                    rationale="Logs often reveal root cause",
                    depth=0
                ),
                Thought(
                    id="t_0_3",
                    content="Approach 3: Check infrastructure/resource constraints",
                    quality=ThoughtQuality.FAIR,
                    rationale="Less likely but possible",
                    depth=0
                )
            ]

        # Generic fallback
        else:
            return [
                Thought(
                    id="t_0_1",
                    content="Approach 1: Systematic analysis of problem constraints",
                    quality=ThoughtQuality.GOOD,
                    rationale="Methodical approach works for most problems",
                    depth=0
                ),
                Thought(
                    id="t_0_2",
                    content="Approach 2: Research best practices and similar solutions",
                    quality=ThoughtQuality.GOOD,
                    rationale="Learn from others' experience",
                    depth=0
                ),
                Thought(
                    id="t_0_3",
                    content="Approach 3: Prototype and test multiple options",
                    quality=ThoughtQuality.FAIR,
                    rationale="Empirical validation but time-consuming",
                    depth=0
                )
            ]

    def _select_best_thoughts(self, thoughts: List[Thought]) -> List[Thought]:
        """
        Select best thoughts to expand based on quality

        Args:
            thoughts: Thoughts at current depth

        Returns:
            Top N thoughts (up to max_branches)
        """
        # Sort by quality (descending)
        sorted_thoughts = sorted(thoughts, key=lambda t: t.quality.value, reverse=True)

        # Return top N (excluding DEAD_END)
        return [
            t for t in sorted_thoughts[:self.max_branches]
            if t.quality != ThoughtQuality.DEAD_END
        ]

    def _expand_thought(self, thought: Thought, problem: str, context: Dict[str, Any]) -> List[Thought]:
        """
        Expand a thought into next-level considerations

        For demonstration, uses template-based expansion.
        In production, would use LLM to generate expansions.
        """
        next_depth = thought.depth + 1

        # Don't expand dead ends or at max depth
        if thought.quality == ThoughtQuality.DEAD_END or next_depth >= self.max_depth:
            return []

        # Example expansion for microservices approach
        if "microservices" in thought.content.lower():
            return [
                Thought(
                    id=f"t_{next_depth}_1_{thought.id}",
                    content="Consider API Gateway + Service Mesh (Istio) for communication",
                    quality=ThoughtQuality.EXCELLENT,
                    rationale="Standard pattern, handles service discovery and load balancing",
                    parent_id=thought.id,
                    depth=next_depth
                ),
                Thought(
                    id=f"t_{next_depth}_2_{thought.id}",
                    content="Use event bus (Kafka) for async communication",
                    quality=ThoughtQuality.GOOD,
                    rationale="Decouples services but adds complexity",
                    parent_id=thought.id,
                    depth=next_depth
                ),
                Thought(
                    id=f"t_{next_depth}_3_{thought.id}",
                    content="Direct REST calls between services",
                    quality=ThoughtQuality.POOR,
                    rationale="Creates tight coupling, hard to scale",
                    parent_id=thought.id,
                    depth=next_depth
                )
            ]

        # Example expansion for serverless approach
        elif "serverless" in thought.content.lower():
            return [
                Thought(
                    id=f"t_{next_depth}_1_{thought.id}",
                    content="Use AWS Lambda + API Gateway + DynamoDB",
                    quality=ThoughtQuality.EXCELLENT,
                    rationale="Fully managed, auto-scaling, pay-per-use",
                    parent_id=thought.id,
                    depth=next_depth
                ),
                Thought(
                    id=f"t_{next_depth}_2_{thought.id}",
                    content="Use Azure Functions + Cosmos DB",
                    quality=ThoughtQuality.GOOD,
                    rationale="Good alternative if already on Azure",
                    parent_id=thought.id,
                    depth=next_depth
                )
            ]

        # Generic expansion
        else:
            return [
                Thought(
                    id=f"t_{next_depth}_1_{thought.id}",
                    content=f"Validate feasibility of: {thought.content}",
                    quality=ThoughtQuality.GOOD,
                    rationale="Need to validate before committing",
                    parent_id=thought.id,
                    depth=next_depth
                )
            ]

    def _select_best_path(self, all_thoughts: List[Thought]) -> List[Thought]:
        """
        Select the best path through the thought tree

        Returns:
            List of thoughts from root to leaf (best path)
        """
        # Find leaf nodes (no children)
        leaf_ids = {t.id for t in all_thoughts}
        for t in all_thoughts:
            if t.parent_id:
                leaf_ids.discard(t.parent_id)

        # Find best leaf by quality
        leaves = [t for t in all_thoughts if t.id in leaf_ids]
        best_leaf = max(leaves, key=lambda t: t.quality.value)

        # Trace back to root
        path = [best_leaf]
        current = best_leaf

        while current.parent_id:
            parent = next(t for t in all_thoughts if t.id == current.parent_id)
            path.insert(0, parent)
            current = parent

        return path

    def _generate_recommendation(self, path: List[Thought], problem: str) -> str:
        """Generate final recommendation based on selected path"""
        recommendation_parts = [
            f"PROBLEM: {problem}",
            "",
            "REASONING PATH:"
        ]

        for i, thought in enumerate(path, 1):
            recommendation_parts.append(
                f"{i}. {thought.content} "
                f"(Quality: {thought.quality.name}, Rationale: {thought.rationale})"
            )

        recommendation_parts.extend([
            "",
            "FINAL RECOMMENDATION:",
            path[-1].content,
            "",
            f"This recommendation is based on {len(path)} levels of evaluation, "
            f"considering {len(path)} alternative approaches at each level."
        ])

        return "\n".join(recommendation_parts)

    def _generate_reasoning_summary(self, selected_path: List[Thought], all_thoughts: List[Thought]) -> str:
        """Generate summary of reasoning process"""
        explored = len(all_thoughts)
        selected = len(selected_path)
        rejected = explored - selected

        return (
            f"Explored {explored} total reasoning paths. "
            f"Selected best path with {selected} steps. "
            f"Rejected {rejected} inferior approaches."
        )

    def _save_result(self, result: TreeOfThoughtsResult):
        """Save ToT result for analysis"""
        from datetime import datetime

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        result_file = self.session_dir / f"tot_result_{timestamp}.json"

        with open(result_file, 'w') as f:
            json.dump({
                "problem": result.problem,
                "selected_path": [t.to_dict() for t in result.selected_path],
                "all_thoughts": [t.to_dict() for t in result.all_thoughts],
                "reasoning_summary": result.reasoning_summary,
                "final_recommendation": result.final_recommendation
            }, f, indent=2)


def main():
    """Example usage and demonstration"""
    print("=== Tree of Thoughts (ToT) Demonstration ===\n")

    # Initialize engine
    engine = TreeOfThoughtsEngine(max_depth=2, max_branches=2)

    # Example 1: System design problem
    problem = "Design a scalable architecture for a high-traffic e-commerce platform"

    print(f"PROBLEM: {problem}\n")
    print("Exploring multiple reasoning paths...\n")

    result = engine.solve(problem)

    print("="*60)
    print("SELECTED REASONING PATH:")
    print("="*60)
    for i, thought in enumerate(result.selected_path, 1):
        print(f"\nStep {i}: {thought.content}")
        print(f"  Quality: {thought.quality.name} ({thought.quality.value}/5)")
        print(f"  Rationale: {thought.rationale}")

    print("\n" + "="*60)
    print("FINAL RECOMMENDATION:")
    print("="*60)
    print(result.final_recommendation)

    print("\n" + "="*60)
    print("REASONING SUMMARY:")
    print("="*60)
    print(result.reasoning_summary)

    print("\n" + "="*60)
    print("COMPARISON TO STANDARD PROMPTING:")
    print("="*60)
    print("Standard Prompting: Would follow ONE path")
    print(f"Tree of Thoughts: Explored {len(result.all_thoughts)} paths, selected best")
    print("\nAdvantage: ToT finds better solutions by exploring alternatives")


if __name__ == "__main__":
    main()
