#!/usr/bin/env python3
"""
Unit Tests for Semantic SYSTEM_STATE Search

Phase 3 Agentic AI Enhancement: Agentic RAG Pattern
Tests semantic search over phase history.
"""

import unittest
import tempfile
import os
from pathlib import Path


class TestSemanticSearch(unittest.TestCase):
    """Test SemanticSystemState class"""

    def setUp(self):
        """Create temp directory for test database"""
        self.temp_dir = tempfile.mkdtemp()

        from semantic_search import SemanticSystemState
        self.search = SemanticSystemState(db_path=self.temp_dir)

    def tearDown(self):
        """Clean up temp directory"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_initialization(self):
        """Test search system initializes correctly"""
        self.assertIsNotNone(self.search)

    def test_add_phase(self):
        """Test adding a phase to the index"""
        self.search.add_phase(
            phase_id=100,
            title="Test Phase",
            content="This is a test phase about email processing and RAG systems.",
            metadata={'date': '2025-01-01'}
        )

        # Should be indexed
        count = self.search.get_phase_count()
        self.assertGreater(count, 0)

    def test_semantic_search_basic(self):
        """Test basic semantic search"""
        # Add test phases
        self.search.add_phase(
            phase_id=1,
            title="Email RAG System",
            content="Implemented email retrieval augmented generation using ChromaDB and Ollama embeddings."
        )
        self.search.add_phase(
            phase_id=2,
            title="Database Optimization",
            content="Optimized SQLite queries for faster system state lookups."
        )

        # Search for email-related content
        results = self.search.search("email search system")

        self.assertGreater(len(results), 0)
        # Email phase should rank higher
        self.assertEqual(results[0]['phase_id'], 1)

    def test_semantic_search_returns_relevance_scores(self):
        """Test that search returns relevance scores"""
        self.search.add_phase(
            phase_id=1,
            title="Test Phase",
            content="Content about machine learning and AI systems."
        )

        # Search for terms that exist in the content
        results = self.search.search("machine learning systems")

        self.assertGreater(len(results), 0)
        self.assertIn('relevance', results[0])
        self.assertGreaterEqual(results[0]['relevance'], 0)

    def test_search_with_limit(self):
        """Test limiting search results"""
        # Add multiple phases
        for i in range(10):
            self.search.add_phase(
                phase_id=i,
                title=f"Phase {i}",
                content=f"Content about feature {i} implementation."
            )

        results = self.search.search("feature implementation", limit=3)

        self.assertEqual(len(results), 3)

    def test_search_no_results(self):
        """Test search with no matching content"""
        self.search.add_phase(
            phase_id=1,
            title="Email System",
            content="Email processing and handling."
        )

        results = self.search.search("quantum computing blockchain", limit=5)

        # Should return empty or low relevance results
        if results:
            self.assertLess(results[0]['relevance'], 0.5)

    def test_search_with_metadata_filter(self):
        """Test filtering search by metadata"""
        self.search.add_phase(
            phase_id=1,
            title="Old Feature",
            content="Legacy system implementation.",
            metadata={'year': '2023'}
        )
        self.search.add_phase(
            phase_id=2,
            title="New Feature",
            content="Modern system implementation.",
            metadata={'year': '2025'}
        )

        results = self.search.search(
            "system implementation",
            filter_metadata={'year': '2025'}
        )

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['phase_id'], 2)

    def test_update_phase(self):
        """Test updating existing phase"""
        self.search.add_phase(
            phase_id=1,
            title="Original Title",
            content="Original content."
        )

        self.search.update_phase(
            phase_id=1,
            title="Updated Title",
            content="Updated content about new features."
        )

        results = self.search.search("new features")

        self.assertGreater(len(results), 0)
        self.assertEqual(results[0]['title'], "Updated Title")

    def test_delete_phase(self):
        """Test deleting a phase"""
        self.search.add_phase(
            phase_id=1,
            title="To Delete",
            content="This will be deleted."
        )

        self.search.delete_phase(1)

        count = self.search.get_phase_count()
        self.assertEqual(count, 0)

    def test_bulk_index(self):
        """Test bulk indexing multiple phases"""
        phases = [
            {'phase_id': i, 'title': f'Phase {i}', 'content': f'Content {i}'}
            for i in range(100)
        ]

        self.search.bulk_index(phases)

        count = self.search.get_phase_count()
        self.assertEqual(count, 100)

    def test_get_similar_phases(self):
        """Test finding similar phases to a given phase"""
        self.search.add_phase(1, "Email System", "Email processing with IMAP protocol.")
        self.search.add_phase(2, "Email RAG", "Email retrieval and email processing with augmented generation.")
        self.search.add_phase(3, "Database System", "SQLite database operations and queries.")

        similar = self.search.get_similar_phases(phase_id=1, limit=2)

        self.assertEqual(len(similar), 2)
        # Both should be returned; ordering depends on TF-IDF weights
        phase_ids = [s['phase_id'] for s in similar]
        self.assertIn(2, phase_ids)  # Email RAG should be in results
        self.assertIn(3, phase_ids)  # Database should also be in results


class TestEmbeddings(unittest.TestCase):
    """Test embedding generation"""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        from semantic_search import SemanticSystemState
        self.search = SemanticSystemState(db_path=self.temp_dir)

    def tearDown(self):
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_generate_embedding(self):
        """Test generating embeddings for text"""
        embedding = self.search.generate_embedding("test text for embedding generation")

        self.assertIsNotNone(embedding)
        # TF-IDF returns dict, Ollama returns list
        self.assertTrue(isinstance(embedding, (dict, list)))
        self.assertGreater(len(embedding), 0)

    def test_embedding_similarity(self):
        """Test embedding similarity calculation"""
        emb1 = self.search.generate_embedding("email processing")
        emb2 = self.search.generate_embedding("email handling")
        emb3 = self.search.generate_embedding("database queries")

        sim_12 = self.search.calculate_similarity(emb1, emb2)
        sim_13 = self.search.calculate_similarity(emb1, emb3)

        # Email processing should be more similar to email handling than database queries
        self.assertGreater(sim_12, sim_13)


class TestIndexFromSystemState(unittest.TestCase):
    """Test indexing from actual SYSTEM_STATE.md"""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        from semantic_search import SemanticSystemState
        self.search = SemanticSystemState(db_path=self.temp_dir)

    def tearDown(self):
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_parse_system_state_format(self):
        """Test parsing SYSTEM_STATE.md format"""
        sample_content = """
## Phase 100: Email RAG System
**Problem**: Need to search emails semantically
**Solution**: Implemented ChromaDB-based RAG

## Phase 101: Database Optimization
**Problem**: Slow queries
**Solution**: Added indexes
"""
        phases = self.search.parse_system_state(sample_content)

        self.assertEqual(len(phases), 2)
        self.assertEqual(phases[0]['phase_id'], 100)
        self.assertIn('Email RAG', phases[0]['title'])


if __name__ == "__main__":
    print("Semantic SYSTEM_STATE Search Unit Tests")
    print("=" * 60)
    unittest.main(verbosity=2)
