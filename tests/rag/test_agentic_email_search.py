#!/usr/bin/env python3
"""
Unit Tests for Agentic Email Search

Tests the iterative RAG logic with mock data (no Mail.app required).
"""

import unittest
from unittest.mock import MagicMock, patch
from agentic_email_search import AgenticEmailSearch, SearchIteration, AgenticSearchResult


class MockRAG:
    """Mock RAG system for testing"""

    def __init__(self, responses=None):
        """
        Args:
            responses: Dict mapping queries to result lists
        """
        self.responses = responses or {}
        self.call_count = 0

    def smart_search(self, query, sender_filter=None, n_results=10):
        self.call_count += 1

        # Return configured response or default
        if query in self.responses:
            return self.responses[query]

        # Default: return diminishing results
        return [
            {
                "subject": f"Test Email {i} for '{query}'",
                "sender": "test@example.com",
                "date": "2025-11-24",
                "relevance": 0.5 - (i * 0.1),
                "message_id": f"msg_{i}"
            }
            for i in range(3)
        ]


class TestAgenticEmailSearch(unittest.TestCase):
    """Test cases for AgenticEmailSearch"""

    def test_initialization(self):
        """Test that searcher initializes with mock RAG"""
        mock_rag = MockRAG()
        searcher = AgenticEmailSearch(rag_instance=mock_rag)

        self.assertEqual(searcher.max_iterations, 3)
        self.assertEqual(searcher.min_relevance_threshold, 0.3)
        self.assertIs(searcher.rag, mock_rag)

    def test_sufficient_results_stops_early(self):
        """Test that search stops when sufficient results found"""
        # Configure mock to return good results
        mock_rag = MockRAG({
            "test query": [
                {"subject": "Relevant email 1", "sender": "a@b.com", "date": "2025-11-24", "relevance": 0.9, "message_id": "1"},
                {"subject": "Relevant email 2", "sender": "a@b.com", "date": "2025-11-24", "relevance": 0.8, "message_id": "2"},
                {"subject": "Relevant email 3", "sender": "a@b.com", "date": "2025-11-24", "relevance": 0.7, "message_id": "3"},
            ]
        })

        searcher = AgenticEmailSearch(rag_instance=mock_rag)

        # Mock LLM to say results are sufficient
        with patch.object(searcher, '_llm_call', return_value='{"sufficient": true, "reasoning": "Good results"}'):
            result = searcher.search("test query", verbose=False)

        self.assertEqual(result.total_iterations, 1)
        self.assertTrue(result.search_successful)
        self.assertEqual(len(result.results), 3)

    def test_iteration_cap_respected(self):
        """Test that search stops at max_iterations"""
        mock_rag = MockRAG()  # Returns default low-relevance results

        searcher = AgenticEmailSearch(
            max_iterations=2,
            rag_instance=mock_rag
        )

        # Mock LLM to always say insufficient and suggest refinement
        with patch.object(searcher, '_llm_call', return_value='{"sufficient": false, "reasoning": "Need more", "refined_query": "better query"}'):
            result = searcher.search("bad query", verbose=False)

        self.assertEqual(result.total_iterations, 2)
        self.assertEqual(mock_rag.call_count, 2)

    def test_no_results_triggers_refinement(self):
        """Test that empty results trigger query refinement"""
        mock_rag = MockRAG({"initial": []})

        searcher = AgenticEmailSearch(rag_instance=mock_rag)

        is_sufficient, reasoning, refinement = searcher._evaluate_sufficiency("initial", [])

        self.assertFalse(is_sufficient)
        self.assertIn("No results", reasoning)
        self.assertIsNotNone(refinement)

    def test_low_relevance_triggers_refinement(self):
        """Test that low relevance results trigger refinement"""
        low_relevance_results = [
            {"subject": "Barely relevant", "sender": "a@b.com", "relevance": 0.1, "message_id": "1"}
        ]

        mock_rag = MockRAG()
        searcher = AgenticEmailSearch(
            min_relevance_threshold=0.3,
            min_results_threshold=2,
            rag_instance=mock_rag
        )

        with patch.object(searcher, '_suggest_query_refinement', return_value="refined query"):
            is_sufficient, reasoning, refinement = searcher._evaluate_sufficiency(
                "test", low_relevance_results
            )

        self.assertFalse(is_sufficient)
        self.assertIn("relevant results", reasoning.lower())

    def test_search_result_structure(self):
        """Test that AgenticSearchResult has correct structure"""
        mock_rag = MockRAG({
            "query": [{"subject": "Test", "sender": "a@b.com", "date": "now", "relevance": 0.9, "message_id": "1"}]
        })

        searcher = AgenticEmailSearch(rag_instance=mock_rag, min_results_threshold=1)

        with patch.object(searcher, '_llm_call', return_value='{"sufficient": true, "reasoning": "ok"}'):
            result = searcher.search("query", verbose=False)

        # Check structure
        self.assertIsInstance(result, AgenticSearchResult)
        self.assertEqual(result.original_query, "query")
        self.assertIsInstance(result.iterations, list)
        self.assertIsInstance(result.iterations[0], SearchIteration)

        # Check serialization
        result_dict = result.to_dict()
        self.assertIn("original_query", result_dict)
        self.assertIn("iterations", result_dict)
        self.assertIn("results", result_dict)

    def test_query_refinement_fallback(self):
        """Test fallback when LLM fails"""
        mock_rag = MockRAG()
        searcher = AgenticEmailSearch(rag_instance=mock_rag)

        # Mock LLM failure
        with patch.object(searcher, '_llm_call', return_value="LLM_ERROR: connection failed"):
            refinement = searcher._suggest_query_refinement("multi word query", [])

        # Should fall back to simplified query
        self.assertEqual(refinement, "multi word")


class TestSearchIteration(unittest.TestCase):
    """Test SearchIteration dataclass"""

    def test_iteration_creation(self):
        iteration = SearchIteration(
            iteration=1,
            query="test",
            results_count=5,
            top_relevance=0.85,
            is_sufficient=True,
            reasoning="Found good results"
        )

        self.assertEqual(iteration.iteration, 1)
        self.assertEqual(iteration.query, "test")
        self.assertTrue(iteration.is_sufficient)


if __name__ == "__main__":
    print("🧪 Agentic Email Search Unit Tests")
    print("=" * 60)
    unittest.main(verbosity=2)
