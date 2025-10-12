#!/usr/bin/env python3
"""
Least-to-Most Prompting: Progressive complexity building from simple to complex

This advanced prompting technique improves problem-solving by:
1. Decomposing complex problems into simpler subproblems
2. Solving subproblems sequentially from easiest to hardest
3. Using solutions from earlier subproblems to solve later ones
4. Building up to the full solution progressively

Use cases:
- Complex multi-step problems
- Hierarchical problem structures
- When simpler solutions inform harder ones
- Educational/explanatory contexts

Reference: "Least-to-Most Prompting Enables Complex Reasoning in Large Language Models"
           Zhou et al., 2022 (ICLR 2023)
"""

import json
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Callable, Any
from datetime import datetime
from pathlib import Path
from enum import Enum

class ComplexityLevel(Enum):
    """Problem complexity level"""
    TRIVIAL = 1
    SIMPLE = 2
    MODERATE = 3
    COMPLEX = 4
    VERY_COMPLEX = 5

@dataclass
class Subproblem:
    """A decomposed subproblem"""
    id: str
    description: str
    complexity: ComplexityLevel
    dependencies: List[str] = field(default_factory=list)  # IDs of prerequisite subproblems
    solution: Optional[str] = None
    reasoning: List[str] = field(default_factory=list)
    solved: bool = False
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

@dataclass
class DecompositionResult:
    """Result of problem decomposition"""
    original_problem: str
    subproblems: List[Subproblem]
    dependency_graph: Dict[str, List[str]]
    solving_order: List[str]
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

@dataclass
class LeastToMostResult:
    """Result of least-to-most solving process"""
    problem: str
    decomposition: DecompositionResult
    solved_subproblems: List[Subproblem]
    final_solution: str
    total_steps: int
    complexity_progression: List[int]
    success: bool
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

class LeastToMostEngine:
    """Engine for least-to-most prompting"""

    def __init__(
        self,
        decomposer: Optional[Callable] = None,
        solver: Optional[Callable] = None
    ):
        """
        Initialize least-to-most engine

        Args:
            decomposer: Custom function to decompose problems
            solver: Custom function to solve subproblems
        """
        self.decomposer = decomposer or self._default_decomposer
        self.solver = solver or self._default_solver

        # Storage
        self.results_dir = Path(__file__).parent.parent.parent / "data" / "least_to_most"
        self.results_dir.mkdir(parents=True, exist_ok=True)
        self.results_file = self.results_dir / "results.json"

    def solve(self, problem: str, context: Optional[Dict] = None) -> LeastToMostResult:
        """
        Apply least-to-most prompting to a problem

        Process:
        1. Decompose problem into subproblems
        2. Determine complexity of each subproblem
        3. Identify dependencies between subproblems
        4. Order subproblems by complexity (least to most)
        5. Solve subproblems sequentially
        6. Use earlier solutions to inform later ones
        7. Synthesize final solution

        Args:
            problem: Complex problem to solve
            context: Optional context for problem

        Returns:
            LeastToMostResult with solution and process details
        """
        # Step 1: Decompose problem
        decomposition = self._decompose_problem(problem, context)

        # Step 2: Solve subproblems in order (least to most complex)
        solved_subproblems = []
        solutions_so_far = {}  # Track solutions for dependency resolution

        for subproblem_id in decomposition.solving_order:
            # Find subproblem
            subproblem = next(sp for sp in decomposition.subproblems if sp.id == subproblem_id)

            # Gather prerequisite solutions
            prerequisite_solutions = {
                dep_id: solutions_so_far[dep_id]
                for dep_id in subproblem.dependencies
                if dep_id in solutions_so_far
            }

            # Solve subproblem using prerequisites
            solution, reasoning = self.solver(
                subproblem=subproblem,
                prerequisites=prerequisite_solutions,
                context=context
            )

            # Update subproblem
            subproblem.solution = solution
            subproblem.reasoning = reasoning
            subproblem.solved = True

            # Track solution
            solutions_so_far[subproblem_id] = solution
            solved_subproblems.append(subproblem)

        # Step 3: Synthesize final solution
        final_solution = self._synthesize_solution(problem, solved_subproblems)

        # Track complexity progression
        complexity_progression = [sp.complexity.value for sp in solved_subproblems]

        result = LeastToMostResult(
            problem=problem,
            decomposition=decomposition,
            solved_subproblems=solved_subproblems,
            final_solution=final_solution,
            total_steps=len(solved_subproblems),
            complexity_progression=complexity_progression,
            success=all(sp.solved for sp in solved_subproblems)
        )

        # Save result
        self._save_result(result)

        return result

    def _decompose_problem(self, problem: str, context: Optional[Dict]) -> DecompositionResult:
        """Decompose problem into subproblems"""
        subproblems = self.decomposer(problem, context)

        # Build dependency graph
        dependency_graph = {sp.id: sp.dependencies for sp in subproblems}

        # Determine solving order (topological sort by complexity)
        solving_order = self._topological_sort(subproblems)

        return DecompositionResult(
            original_problem=problem,
            subproblems=subproblems,
            dependency_graph=dependency_graph,
            solving_order=solving_order
        )

    def _topological_sort(self, subproblems: List[Subproblem]) -> List[str]:
        """
        Sort subproblems by:
        1. Dependency order (prerequisites first)
        2. Complexity (least to most)
        """
        # Build adjacency list
        graph = {sp.id: sp.dependencies for sp in subproblems}
        subproblem_map = {sp.id: sp for sp in subproblems}

        # Find nodes with no dependencies (starting points)
        no_deps = [sp_id for sp_id, deps in graph.items() if not deps]

        # Sort by complexity within each level
        sorted_order = []
        visited = set()

        def visit(sp_id: str):
            if sp_id in visited:
                return
            visited.add(sp_id)

            # Visit dependencies first
            for dep_id in graph[sp_id]:
                visit(dep_id)

            sorted_order.append(sp_id)

        # Visit all nodes, starting with no-dependency nodes sorted by complexity
        no_deps_sorted = sorted(no_deps, key=lambda sp_id: subproblem_map[sp_id].complexity.value)
        for sp_id in no_deps_sorted:
            visit(sp_id)

        # Visit any remaining nodes (circular dependencies handled)
        for sp_id in graph.keys():
            if sp_id not in visited:
                visit(sp_id)

        return sorted_order

    def _default_decomposer(self, problem: str, context: Optional[Dict]) -> List[Subproblem]:
        """
        Default problem decomposer (heuristic-based)

        In production, this would use LLM to decompose problems
        """
        # Mock decomposition for demonstration
        if "e-commerce" in problem.lower() or "shopping" in problem.lower():
            return [
                Subproblem(
                    id="sp1",
                    description="Define product catalog data model",
                    complexity=ComplexityLevel.SIMPLE,
                    dependencies=[]
                ),
                Subproblem(
                    id="sp2",
                    description="Design user authentication system",
                    complexity=ComplexityLevel.SIMPLE,
                    dependencies=[]
                ),
                Subproblem(
                    id="sp3",
                    description="Build shopping cart functionality",
                    complexity=ComplexityLevel.MODERATE,
                    dependencies=["sp1", "sp2"]  # Needs products and users
                ),
                Subproblem(
                    id="sp4",
                    description="Implement payment processing",
                    complexity=ComplexityLevel.COMPLEX,
                    dependencies=["sp2", "sp3"]  # Needs users and cart
                ),
                Subproblem(
                    id="sp5",
                    description="Add order tracking and notifications",
                    complexity=ComplexityLevel.MODERATE,
                    dependencies=["sp4"]  # Needs payment completed
                ),
                Subproblem(
                    id="sp6",
                    description="Scale for 1M+ concurrent users",
                    complexity=ComplexityLevel.VERY_COMPLEX,
                    dependencies=["sp3", "sp4", "sp5"]  # Needs core features first
                )
            ]
        elif "api" in problem.lower():
            return [
                Subproblem(
                    id="sp1",
                    description="Define API resource models and endpoints",
                    complexity=ComplexityLevel.SIMPLE,
                    dependencies=[]
                ),
                Subproblem(
                    id="sp2",
                    description="Implement authentication and authorization",
                    complexity=ComplexityLevel.MODERATE,
                    dependencies=[]
                ),
                Subproblem(
                    id="sp3",
                    description="Add rate limiting and throttling",
                    complexity=ComplexityLevel.MODERATE,
                    dependencies=["sp1", "sp2"]
                ),
                Subproblem(
                    id="sp4",
                    description="Implement versioning strategy",
                    complexity=ComplexityLevel.COMPLEX,
                    dependencies=["sp1"]
                ),
                Subproblem(
                    id="sp5",
                    description="Add monitoring and analytics",
                    complexity=ComplexityLevel.COMPLEX,
                    dependencies=["sp3", "sp4"]
                )
            ]
        else:
            # Generic decomposition
            return [
                Subproblem(
                    id="sp1",
                    description="Understand core requirements",
                    complexity=ComplexityLevel.SIMPLE,
                    dependencies=[]
                ),
                Subproblem(
                    id="sp2",
                    description="Design basic solution",
                    complexity=ComplexityLevel.MODERATE,
                    dependencies=["sp1"]
                ),
                Subproblem(
                    id="sp3",
                    description="Add advanced features",
                    complexity=ComplexityLevel.COMPLEX,
                    dependencies=["sp2"]
                )
            ]

    def _default_solver(
        self,
        subproblem: Subproblem,
        prerequisites: Dict[str, str],
        context: Optional[Dict]
    ) -> tuple[str, List[str]]:
        """
        Default subproblem solver (mock implementation)

        In production, this would use LLM to solve subproblems
        """
        # Mock solutions based on subproblem
        solution_map = {
            # E-commerce solutions
            "sp1": (
                "Product catalog: PostgreSQL with tables (products, categories, inventory, pricing)",
                ["Define product schema", "Add indexing for search", "Include inventory tracking"]
            ),
            "sp2": (
                "Authentication: JWT tokens with OAuth2, store users in PostgreSQL",
                ["Implement user registration", "Add login/logout", "Include password reset"]
            ),
            "sp3": (
                f"Shopping cart: Redis for session storage, sync to PostgreSQL. "
                f"Uses product data from: {prerequisites.get('sp1', 'N/A')} and "
                f"user auth from: {prerequisites.get('sp2', 'N/A')}",
                ["Add to cart endpoint", "Update quantities", "Cart persistence", "Leverage product catalog", "Verify user auth"]
            ),
            "sp4": (
                f"Payment: Stripe API integration with webhook handling. "
                f"Cart data from: {prerequisites.get('sp3', 'N/A')}",
                ["Integrate Stripe SDK", "Create payment intent", "Handle webhooks", "Use cart totals", "Verify user identity"]
            ),
            "sp5": (
                f"Notifications: SendGrid for email, Twilio for SMS. "
                f"Triggered after payment from: {prerequisites.get('sp4', 'N/A')}",
                ["Email order confirmation", "SMS shipping updates", "Track order status", "Use payment completion event"]
            ),
            "sp6": (
                f"Scaling: Load balancer + Redis + Read replicas + CDN. "
                f"Applied to cart ({prerequisites.get('sp3', 'N/A')}), "
                f"payment ({prerequisites.get('sp4', 'N/A')}), and "
                f"notifications ({prerequisites.get('sp5', 'N/A')})",
                ["Add load balancer", "Scale Redis cluster", "Add PostgreSQL replicas", "CDN for static assets", "Leverage existing cart/payment/notification systems"]
            ),

            # API solutions
            # (similar pattern for API problem)
        }

        # Get solution or generate generic one
        if subproblem.id in solution_map:
            solution, reasoning = solution_map[subproblem.id]
        else:
            solution = f"Solution for: {subproblem.description}"
            reasoning = ["Analyze problem", "Design solution", "Implement"]

            # Add prerequisite context
            if prerequisites:
                solution += f" (Building on: {', '.join(prerequisites.keys())})"
                reasoning.append(f"Leverage prerequisites: {', '.join(prerequisites.keys())}")

        return solution, reasoning

    def _synthesize_solution(self, problem: str, solved_subproblems: List[Subproblem]) -> str:
        """Synthesize final solution from solved subproblems"""
        solution = f"Complete solution for: {problem}\n\n"

        solution += "Sequential solution approach:\n"
        for i, sp in enumerate(solved_subproblems, 1):
            solution += f"\n{i}. {sp.description} (Complexity: {sp.complexity.name})\n"
            solution += f"   Solution: {sp.solution}\n"
            if sp.dependencies:
                solution += f"   Built upon: {', '.join(sp.dependencies)}\n"

        solution += "\nFinal integrated solution:\n"
        solution += "All components work together: "
        solution += " → ".join([sp.description for sp in solved_subproblems])

        return solution

    def _save_result(self, result: LeastToMostResult):
        """Save result to persistent storage"""
        # Load existing results
        results = []
        if self.results_file.exists():
            with open(self.results_file, 'r') as f:
                results = json.load(f)

        # Add new result (simplified for JSON)
        result_dict = {
            'problem': result.problem,
            'total_steps': result.total_steps,
            'complexity_progression': result.complexity_progression,
            'success': result.success,
            'timestamp': result.timestamp,
            'subproblems': [
                {
                    'id': sp.id,
                    'description': sp.description,
                    'complexity': sp.complexity.name,
                    'dependencies': sp.dependencies,
                    'solved': sp.solved
                }
                for sp in result.solved_subproblems
            ]
        }
        results.append(result_dict)

        # Save
        with open(self.results_file, 'w') as f:
            json.dump(results, f, indent=2)

def demo():
    """Demonstrate least-to-most engine"""
    print("=" * 80)
    print("Least-to-Most Prompting Engine Demo")
    print("=" * 80)

    engine = LeastToMostEngine()

    # Test Case 1: E-commerce platform
    print("\n📋 Test Case 1: Build E-commerce Platform")
    print("-" * 80)
    problem1 = "Build a complete e-commerce platform for 1M+ concurrent users"

    result1 = engine.solve(problem1)

    print(f"Problem: {result1.problem}")
    print(f"\n📊 Decomposition:")
    print(f"   - Total subproblems: {result1.total_steps}")
    print(f"   - Complexity progression: {' → '.join(map(str, result1.complexity_progression))}")
    print(f"   - Success: {result1.success}")

    print(f"\n🔄 Solving Order (Least to Most Complex):")
    for i, sp in enumerate(result1.solved_subproblems, 1):
        deps = f" (depends on: {', '.join(sp.dependencies)})" if sp.dependencies else " (no dependencies)"
        print(f"   {i}. [{sp.complexity.name}] {sp.description}{deps}")

    print(f"\n🎯 Solutions (showing how each builds on previous):")
    for i, sp in enumerate(result1.solved_subproblems[:3], 1):  # Show first 3
        print(f"\n   Step {i}: {sp.description}")
        print(f"   Complexity: {sp.complexity.name}")
        if sp.dependencies:
            print(f"   Prerequisites: {', '.join(sp.dependencies)}")
        print(f"   Solution: {sp.solution}")
        print(f"   Reasoning steps: {len(sp.reasoning)}")

    print(f"\n   ... (3 more subproblems) ...")

    # Show final subproblem (most complex)
    final_sp = result1.solved_subproblems[-1]
    print(f"\n   Step {result1.total_steps}: {final_sp.description}")
    print(f"   Complexity: {final_sp.complexity.name}")
    print(f"   Prerequisites: {', '.join(final_sp.dependencies)}")
    print(f"   Solution: {final_sp.solution}")

    # Test Case 2: API Design
    print("\n" + "=" * 80)
    print("📋 Test Case 2: Design RESTful API")
    print("-" * 80)
    problem2 = "Design a production-ready RESTful API with versioning and monitoring"

    result2 = engine.solve(problem2)

    print(f"Problem: {result2.problem}")
    print(f"\n📊 Decomposition:")
    print(f"   - Total subproblems: {result2.total_steps}")
    print(f"   - Complexity progression: {' → '.join(map(str, result2.complexity_progression))}")

    print(f"\n🔄 Solving Order:")
    for i, sp in enumerate(result2.solved_subproblems, 1):
        deps = f" (depends on: {', '.join(sp.dependencies)})" if sp.dependencies else ""
        print(f"   {i}. [{sp.complexity.name}] {sp.description}{deps}")

    # Comparison: Least-to-Most vs Direct Approach
    print("\n" + "=" * 80)
    print("📊 Least-to-Most vs Direct Approach Comparison")
    print("-" * 80)
    print(f"\n❌ Direct Approach (typical failure):")
    print(f"   - Attempt to solve entire problem at once")
    print(f"   - Often miss dependencies or ordering")
    print(f"   - Higher risk of incomplete solution")
    print(f"   - Example: 'Build e-commerce platform' → overwhelmed by complexity")

    print(f"\n✅ Least-to-Most Approach (systematic success):")
    print(f"   - Decompose into {result1.total_steps} manageable subproblems")
    print(f"   - Solve in order: {' → '.join(map(str, result1.complexity_progression))}")
    print(f"   - Each solution builds on previous ones")
    print(f"   - Clear dependency tracking: {len(result1.decomposition.dependency_graph)} nodes")
    print(f"   - Success rate: {100 if result1.success else 0}%")

    print(f"\n💡 Benefits:")
    print(f"   - Handles complex multi-step problems")
    print(f"   - Ensures prerequisites solved first")
    print(f"   - Progressive complexity builds confidence")
    print(f"   - Reusable solutions for later steps")

    print("\n" + "=" * 80)
    print("✅ Demo Complete")
    print("=" * 80)
    print(f"\nResults saved to: {engine.results_file}")

if __name__ == "__main__":
    demo()
