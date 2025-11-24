#!/usr/bin/env python3
"""
Agentic Email Search - Iterative RAG with Self-Evaluation

Implements the Agentic RAG pattern:
  Query -> Retrieve -> Evaluate sufficiency -> Refine query -> Repeat until satisfied

Key Features:
- Self-evaluation: LLM judges if results are sufficient for the query
- Query refinement: LLM generates improved queries when results insufficient
- Iteration cap: Maximum 3 iterations to prevent infinite loops
- Reasoning chain: Full transparency on search evolution

Author: Maia System
Created: 2025-11-24 (Agentic AI Enhancement Project - Phase 1)
"""

import os
import sys
import json
import requests
from pathlib import Path
from typing import List, Dict, Optional, Any, Tuple
from dataclasses import dataclass, field, asdict
from datetime import datetime

MAIA_ROOT = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(MAIA_ROOT))

from claude.tools.email_rag_ollama import EmailRAGOllama


@dataclass
class SearchIteration:
    """Record of a single search iteration"""
    iteration: int
    query: str
    results_count: int
    top_relevance: float
    is_sufficient: bool
    reasoning: str
    refinement_suggestion: Optional[str] = None


@dataclass
class AgenticSearchResult:
    """Complete result of an agentic search"""
    original_query: str
    final_query: str
    iterations: List[SearchIteration]
    total_iterations: int
    results: List[Dict[str, Any]]
    search_successful: bool
    summary: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "original_query": self.original_query,
            "final_query": self.final_query,
            "iterations": [asdict(i) for i in self.iterations],
            "total_iterations": self.total_iterations,
            "results": self.results,
            "search_successful": self.search_successful,
            "summary": self.summary
        }


class AgenticEmailSearch:
    """
    Agentic Email RAG with iterative query refinement.

    Pattern: Query -> Retrieve -> Evaluate -> Refine -> Repeat (max 3x)

    Uses local LLM (llama3.2:3b) for:
    - Evaluating if search results are sufficient
    - Generating refined queries when results insufficient
    """

    def __init__(
        self,
        max_iterations: int = 3,
        min_relevance_threshold: float = 0.3,
        min_results_threshold: int = 2,
        evaluation_model: str = "llama3.2:3b",
        rag_instance: Optional[Any] = None
    ):
        """
        Initialize Agentic Email Search.

        Args:
            max_iterations: Maximum search iterations (default: 3)
            min_relevance_threshold: Minimum relevance score to consider (default: 0.3)
            min_results_threshold: Minimum results needed for sufficiency (default: 2)
            evaluation_model: Ollama model for evaluation (default: llama3.2:3b)
            rag_instance: Optional pre-initialized RAG instance (for testing/DI)
        """
        self.max_iterations = max_iterations
        self.min_relevance_threshold = min_relevance_threshold
        self.min_results_threshold = min_results_threshold
        self.evaluation_model = evaluation_model
        self.ollama_url = "http://localhost:11434"

        # Initialize underlying RAG system (or use injected instance)
        if rag_instance is not None:
            self.rag = rag_instance
        else:
            self.rag = EmailRAGOllama()

    def _llm_call(self, prompt: str) -> str:
        """Make a call to local LLM"""
        try:
            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json={
                    "model": self.evaluation_model,
                    "prompt": prompt,
                    "stream": False
                },
                timeout=30
            )
            response.raise_for_status()
            return response.json()["response"].strip()
        except Exception as e:
            return f"LLM_ERROR: {str(e)}"

    def _evaluate_sufficiency(
        self,
        query: str,
        results: List[Dict[str, Any]]
    ) -> Tuple[bool, str, Optional[str]]:
        """
        Evaluate if search results are sufficient for the query.

        Returns:
            Tuple of (is_sufficient, reasoning, refinement_suggestion)
        """
        if not results:
            return False, "No results found", f"Try broader search: {query.split()[0] if query.split() else query}"

        # Check basic thresholds
        relevant_results = [r for r in results if r.get('relevance', 0) >= self.min_relevance_threshold]

        if len(relevant_results) < self.min_results_threshold:
            # Use LLM to suggest refinement
            refinement = self._suggest_query_refinement(query, results)
            return False, f"Only {len(relevant_results)} relevant results (need {self.min_results_threshold})", refinement

        # Use LLM to evaluate semantic sufficiency
        results_summary = "\n".join([
            f"- {r['subject'][:60]} (relevance: {r.get('relevance', 0):.0%})"
            for r in results[:5]
        ])

        prompt = f"""Evaluate if these email search results adequately answer the query.

QUERY: "{query}"

TOP RESULTS:
{results_summary}

Answer with JSON only:
{{"sufficient": true/false, "reasoning": "brief explanation", "refined_query": "better query if not sufficient, null if sufficient"}}"""

        response = self._llm_call(prompt)

        try:
            # Parse JSON response
            # Handle potential markdown code blocks
            if "```" in response:
                response = response.split("```")[1]
                if response.startswith("json"):
                    response = response[4:]

            evaluation = json.loads(response.strip())
            return (
                evaluation.get("sufficient", True),
                evaluation.get("reasoning", "LLM evaluation complete"),
                evaluation.get("refined_query")
            )
        except (json.JSONDecodeError, KeyError):
            # Fallback: if we have enough results, consider sufficient
            if len(relevant_results) >= self.min_results_threshold:
                return True, "Sufficient results found (fallback evaluation)", None
            return False, "Could not parse LLM response, insufficient results", None

    def _suggest_query_refinement(
        self,
        original_query: str,
        current_results: List[Dict[str, Any]]
    ) -> str:
        """Use LLM to suggest a refined query"""
        context = ""
        if current_results:
            context = f"\nCurrent results (low relevance):\n" + "\n".join([
                f"- {r['subject'][:50]}" for r in current_results[:3]
            ])

        prompt = f"""The search query "{original_query}" returned poor results.
{context}

Suggest ONE refined search query that might find better email results.
Consider: synonyms, related terms, broader/narrower scope, different phrasing.

Reply with ONLY the refined query, nothing else."""

        refined = self._llm_call(prompt)

        # Clean up response
        refined = refined.strip().strip('"').strip("'")

        # Fallback if LLM fails
        if "LLM_ERROR" in refined or len(refined) > 100:
            words = original_query.split()
            if len(words) > 2:
                return " ".join(words[:2])  # Simplify to first two words
            return original_query

        return refined

    def search(
        self,
        query: str,
        n_results: int = 10,
        sender_filter: Optional[str] = None,
        verbose: bool = True
    ) -> AgenticSearchResult:
        """
        Perform agentic email search with iterative refinement.

        Args:
            query: Initial search query
            n_results: Number of results to return
            sender_filter: Optional sender email filter
            verbose: Print progress (default: True)

        Returns:
            AgenticSearchResult with full search history and final results
        """
        iterations: List[SearchIteration] = []
        current_query = query
        best_results: List[Dict[str, Any]] = []

        if verbose:
            print(f"\n🔍 Agentic Email Search: \"{query}\"")
            print("=" * 60)

        for iteration in range(1, self.max_iterations + 1):
            if verbose:
                print(f"\n📍 Iteration {iteration}/{self.max_iterations}")
                print(f"   Query: \"{current_query}\"")

            # Perform search
            results = self.rag.smart_search(
                query=current_query,
                sender_filter=sender_filter,
                n_results=n_results
            )

            if verbose:
                print(f"   Results: {len(results)} emails found")

            # Track best results seen
            if len(results) > len(best_results):
                best_results = results
            elif results and (not best_results or
                  results[0].get('relevance', 0) > best_results[0].get('relevance', 0)):
                best_results = results

            # Evaluate sufficiency
            is_sufficient, reasoning, refinement = self._evaluate_sufficiency(
                current_query, results
            )

            top_relevance = results[0].get('relevance', 0) if results else 0.0

            iteration_record = SearchIteration(
                iteration=iteration,
                query=current_query,
                results_count=len(results),
                top_relevance=top_relevance,
                is_sufficient=is_sufficient,
                reasoning=reasoning,
                refinement_suggestion=refinement
            )
            iterations.append(iteration_record)

            if verbose:
                status = "✅ Sufficient" if is_sufficient else "🔄 Refining"
                print(f"   Evaluation: {status}")
                print(f"   Reasoning: {reasoning}")

            if is_sufficient:
                break

            # Refine query for next iteration
            if refinement and iteration < self.max_iterations:
                current_query = refinement
                if verbose:
                    print(f"   → Refined query: \"{refinement}\"")

        # Build summary
        if iterations[-1].is_sufficient:
            summary = f"Found {len(best_results)} relevant emails in {len(iterations)} iteration(s)"
        else:
            summary = f"Best effort: {len(best_results)} results after {len(iterations)} iterations (may be incomplete)"

        result = AgenticSearchResult(
            original_query=query,
            final_query=current_query,
            iterations=iterations,
            total_iterations=len(iterations),
            results=best_results[:n_results],
            search_successful=iterations[-1].is_sufficient,
            summary=summary
        )

        if verbose:
            print("\n" + "=" * 60)
            print(f"📊 {summary}")
            if best_results:
                print(f"\n📧 Top Results:")
                for i, r in enumerate(best_results[:5], 1):
                    print(f"   {i}. {r['subject'][:55]}...")
                    print(f"      From: {r['sender'][:40]} | Relevance: {r.get('relevance', 0):.0%}")

        return result

    def search_comprehensive(
        self,
        query: str,
        n_results: int = 20,
        verbose: bool = True
    ) -> AgenticSearchResult:
        """
        Comprehensive search that tries multiple query variations.

        Use for broad queries like "find all emails about Project X"
        """
        if verbose:
            print(f"\n🔎 Comprehensive Agentic Search: \"{query}\"")
            print("=" * 60)

        # Generate query variations
        variations_prompt = f"""Generate 3 different search query variations for finding emails about: "{query}"

Consider: different phrasings, key terms, related concepts.

Reply with JSON array only: ["query1", "query2", "query3"]"""

        response = self._llm_call(variations_prompt)

        try:
            if "```" in response:
                response = response.split("```")[1]
                if response.startswith("json"):
                    response = response[4:]
            variations = json.loads(response.strip())
            if not isinstance(variations, list):
                variations = [query]
        except:
            variations = [query]

        # Include original query
        all_queries = [query] + [v for v in variations if v != query][:2]

        if verbose:
            print(f"   Query variations: {all_queries}")

        # Collect all unique results
        all_results: Dict[str, Dict] = {}
        all_iterations: List[SearchIteration] = []

        for q in all_queries:
            result = self.search(q, n_results=n_results // 2, verbose=False)
            all_iterations.extend(result.iterations)

            for r in result.results:
                msg_id = r.get('message_id', r.get('subject', ''))
                if msg_id not in all_results:
                    all_results[msg_id] = r

        # Sort by relevance
        final_results = sorted(
            all_results.values(),
            key=lambda x: x.get('relevance', 0),
            reverse=True
        )[:n_results]

        summary = f"Comprehensive search found {len(final_results)} unique emails across {len(all_queries)} query variations"

        if verbose:
            print(f"\n📊 {summary}")
            print(f"\n📧 Top Results:")
            for i, r in enumerate(final_results[:5], 1):
                print(f"   {i}. {r['subject'][:55]}...")

        return AgenticSearchResult(
            original_query=query,
            final_query=f"[{len(all_queries)} variations]",
            iterations=all_iterations,
            total_iterations=len(all_iterations),
            results=final_results,
            search_successful=len(final_results) >= self.min_results_threshold,
            summary=summary
        )


def main():
    """Demo and test the Agentic Email Search"""
    import argparse

    parser = argparse.ArgumentParser(description="Agentic Email Search")
    parser.add_argument("query", nargs="?", default="project deadline", help="Search query")
    parser.add_argument("--comprehensive", "-c", action="store_true", help="Use comprehensive search")
    parser.add_argument("--results", "-n", type=int, default=10, help="Number of results")
    parser.add_argument("--json", action="store_true", help="Output as JSON")

    args = parser.parse_args()

    print("🤖 Agentic Email Search - Iterative RAG System")
    print("=" * 60)

    try:
        searcher = AgenticEmailSearch()

        if args.comprehensive:
            result = searcher.search_comprehensive(args.query, n_results=args.results)
        else:
            result = searcher.search(args.query, n_results=args.results)

        if args.json:
            print("\n" + json.dumps(result.to_dict(), indent=2))

        print("\n✅ Agentic search complete!")
        return 0

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit(main())
