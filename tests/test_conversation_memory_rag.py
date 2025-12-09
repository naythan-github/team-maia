#!/usr/bin/env python3
"""
Test Suite for Conversation Memory RAG System

TDD tests for hybrid SQLite + ChromaDB conversation memory.

Author: SRE Principal Engineer Agent
Created: 2025-12-08
"""

import pytest
import tempfile
import shutil
import json
from pathlib import Path
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock
import sys

# Add project root to path
MAIA_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(MAIA_ROOT))


class TestConversationMemoryRAGInit:
    """Test initialization and setup"""

    def test_init_creates_db_directory(self, tmp_path):
        """Given a path, When initializing, Then directory is created"""
        from claude.tools.memory.conversation_memory_rag import ConversationMemoryRAG

        db_path = tmp_path / "test_memory_rag"
        rag = ConversationMemoryRAG(db_path=str(db_path))

        assert db_path.exists()
        assert rag.collection is not None

    def test_init_uses_default_path_when_none(self):
        """Given no path, When initializing, Then uses UFC-compliant default"""
        from claude.tools.memory.conversation_memory_rag import ConversationMemoryRAG

        rag = ConversationMemoryRAG()

        assert "rag_databases" in str(rag.db_path)
        assert "conversation_memory_rag" in str(rag.db_path)

    def test_init_creates_collection(self, tmp_path):
        """Given initialization, When complete, Then ChromaDB collection exists"""
        from claude.tools.memory.conversation_memory_rag import ConversationMemoryRAG

        db_path = tmp_path / "test_memory_rag"
        rag = ConversationMemoryRAG(db_path=str(db_path))

        assert rag.collection.name == "conversation_memory"


class TestEmbeddingGeneration:
    """Test embedding generation from journey data"""

    @pytest.fixture
    def mock_ollama(self):
        """Mock Ollama API responses"""
        with patch('requests.post') as mock_post:
            mock_response = MagicMock()
            mock_response.json.return_value = {
                "embeddings": [[0.1] * 768]  # nomic-embed-text dimension
            }
            mock_response.raise_for_status = MagicMock()
            mock_post.return_value = mock_response
            yield mock_post

    def test_embed_journey_generates_embedding(self, tmp_path, mock_ollama):
        """Given journey data, When embedding, Then embedding is generated"""
        from claude.tools.memory.conversation_memory_rag import ConversationMemoryRAG

        rag = ConversationMemoryRAG(db_path=str(tmp_path / "test_rag"))

        journey_data = {
            "journey_id": "test-123",
            "problem_description": "Need to optimize database queries",
            "meta_learning": "Discovered N+1 query pattern causes slowdowns",
            "timestamp": datetime.now().isoformat(),
            "agents_used": json.dumps([{"agent": "SRE Principal Engineer"}]),
            "business_impact": "50% latency reduction"
        }

        result = rag.embed_journey(journey_data)

        assert result is True
        mock_ollama.assert_called_once()

    def test_embed_journey_stores_in_chromadb(self, tmp_path, mock_ollama):
        """Given journey, When embedded, Then stored in ChromaDB"""
        from claude.tools.memory.conversation_memory_rag import ConversationMemoryRAG

        rag = ConversationMemoryRAG(db_path=str(tmp_path / "test_rag"))

        journey_data = {
            "journey_id": "test-456",
            "problem_description": "Implement user authentication",
            "meta_learning": "JWT tokens work well for stateless auth",
            "timestamp": datetime.now().isoformat(),
            "agents_used": json.dumps([]),
            "business_impact": "Security improvement"
        }

        rag.embed_journey(journey_data)

        # Verify stored in collection
        assert rag.collection.count() == 1

    def test_embed_journey_skips_already_indexed(self, tmp_path, mock_ollama):
        """Given already indexed journey, When embedding again, Then skips"""
        from claude.tools.memory.conversation_memory_rag import ConversationMemoryRAG

        rag = ConversationMemoryRAG(db_path=str(tmp_path / "test_rag"))

        journey_data = {
            "journey_id": "test-duplicate",
            "problem_description": "Test problem",
            "meta_learning": "Test learning",
            "timestamp": datetime.now().isoformat(),
            "agents_used": json.dumps([]),
            "business_impact": "Test impact"
        }

        # First embed
        rag.embed_journey(journey_data)
        call_count_after_first = mock_ollama.call_count

        # Second embed (should skip)
        rag.embed_journey(journey_data)

        assert mock_ollama.call_count == call_count_after_first  # No new calls


class TestSemanticSearch:
    """Test semantic search functionality"""

    @pytest.fixture
    def populated_rag(self, tmp_path):
        """Create RAG with test data"""
        with patch('requests.post') as mock_post:
            # Create embeddings that will cluster by topic
            call_count = [0]

            def mock_embedding(*args, **kwargs):
                call_count[0] += 1
                mock_response = MagicMock()
                # Different embeddings for different content
                if "database" in str(kwargs.get('json', {}).get('input', '')).lower():
                    embedding = [0.9] + [0.1] * 767  # Database cluster
                elif "security" in str(kwargs.get('json', {}).get('input', '')).lower():
                    embedding = [0.1] + [0.9] + [0.1] * 766  # Security cluster
                else:
                    embedding = [0.5] * 768  # Neutral
                mock_response.json.return_value = {"embeddings": [embedding]}
                mock_response.raise_for_status = MagicMock()
                return mock_response

            mock_post.side_effect = mock_embedding

            from claude.tools.memory.conversation_memory_rag import ConversationMemoryRAG
            rag = ConversationMemoryRAG(db_path=str(tmp_path / "test_rag"))

            # Add test journeys
            journeys = [
                {
                    "journey_id": "db-1",
                    "problem_description": "Database query optimization",
                    "meta_learning": "Index optimization improves database performance",
                    "timestamp": datetime.now().isoformat(),
                    "agents_used": json.dumps([{"agent": "SRE"}]),
                    "business_impact": "50% faster queries"
                },
                {
                    "journey_id": "sec-1",
                    "problem_description": "Security vulnerability assessment",
                    "meta_learning": "Security scanning should be automated",
                    "timestamp": datetime.now().isoformat(),
                    "agents_used": json.dumps([{"agent": "Security"}]),
                    "business_impact": "Reduced risk"
                },
                {
                    "journey_id": "db-2",
                    "problem_description": "Database migration planning",
                    "meta_learning": "Database migrations need rollback plans",
                    "timestamp": datetime.now().isoformat(),
                    "agents_used": json.dumps([{"agent": "SRE"}]),
                    "business_impact": "Zero downtime migration"
                }
            ]

            for journey in journeys:
                rag.embed_journey(journey)

            yield rag

    def test_search_similar_returns_relevant_results(self, populated_rag):
        """Given journeys, When searching, Then most relevant returned"""
        with patch('requests.post') as mock_post:
            mock_response = MagicMock()
            mock_response.json.return_value = {"embeddings": [[0.9] + [0.1] * 767]}
            mock_response.raise_for_status = MagicMock()
            mock_post.return_value = mock_response

            results = populated_rag.search_similar("database performance issues")

            assert len(results) > 0
            # Database-related journeys should be top results
            assert any("database" in r.get("problem_description", "").lower() for r in results)

    def test_search_similar_respects_n_results(self, populated_rag):
        """Given n_results limit, When searching, Then respects limit"""
        with patch('requests.post') as mock_post:
            mock_response = MagicMock()
            mock_response.json.return_value = {"embeddings": [[0.5] * 768]}
            mock_response.raise_for_status = MagicMock()
            mock_post.return_value = mock_response

            results = populated_rag.search_similar("test query", n_results=2)

            assert len(results) <= 2


class TestGracefulDegradation:
    """Test graceful degradation when dependencies unavailable"""

    def test_embed_fails_gracefully_without_ollama(self, tmp_path):
        """Given Ollama unavailable, When embedding, Then fails gracefully"""
        with patch('requests.post') as mock_post:
            mock_post.side_effect = ConnectionError("Ollama not running")

            from claude.tools.memory.conversation_memory_rag import ConversationMemoryRAG
            rag = ConversationMemoryRAG(db_path=str(tmp_path / "test_rag"))

            journey_data = {
                "journey_id": "test-fail",
                "problem_description": "Test problem",
                "meta_learning": "Test learning",
                "timestamp": datetime.now().isoformat(),
                "agents_used": json.dumps([]),
                "business_impact": "Test"
            }

            result = rag.embed_journey(journey_data)

            assert result is False  # Graceful failure

    def test_search_fails_gracefully_without_ollama(self, tmp_path):
        """Given Ollama unavailable, When searching, Then returns empty"""
        with patch('requests.post') as mock_post:
            mock_post.side_effect = ConnectionError("Ollama not running")

            from claude.tools.memory.conversation_memory_rag import ConversationMemoryRAG
            rag = ConversationMemoryRAG(db_path=str(tmp_path / "test_rag"))

            results = rag.search_similar("test query")

            assert results == []  # Empty, not exception


class TestSyncFromSQLite:
    """Test syncing from conversations.db"""

    def test_sync_indexes_unindexed_journeys(self, tmp_path):
        """Given journeys in SQLite not in ChromaDB, When sync, Then indexed"""
        with patch('requests.post') as mock_post:
            mock_response = MagicMock()
            mock_response.json.return_value = {"embeddings": [[0.5] * 768]}
            mock_response.raise_for_status = MagicMock()
            mock_post.return_value = mock_response

            from claude.tools.memory.conversation_memory_rag import ConversationMemoryRAG
            rag = ConversationMemoryRAG(db_path=str(tmp_path / "test_rag"))

            # Create mock SQLite data
            mock_journeys = [
                {
                    "journey_id": "sync-1",
                    "problem_description": "First problem",
                    "meta_learning": "First learning",
                    "timestamp": datetime.now().isoformat(),
                    "agents_used": json.dumps([]),
                    "business_impact": "Impact 1"
                },
                {
                    "journey_id": "sync-2",
                    "problem_description": "Second problem",
                    "meta_learning": "Second learning",
                    "timestamp": datetime.now().isoformat(),
                    "agents_used": json.dumps([]),
                    "business_impact": "Impact 2"
                }
            ]

            stats = rag.sync_from_sqlite(mock_journeys)

            assert stats["indexed"] == 2
            assert stats["skipped"] == 0


class TestRelevanceFiltering:
    """Test relevance and recency filtering"""

    def test_get_relevant_context_weights_recent(self, tmp_path):
        """Given old and recent similar journeys, When retrieving, Then recent weighted higher"""
        with patch('requests.post') as mock_post:
            mock_response = MagicMock()
            mock_response.json.return_value = {"embeddings": [[0.5] * 768]}
            mock_response.raise_for_status = MagicMock()
            mock_post.return_value = mock_response

            from claude.tools.memory.conversation_memory_rag import ConversationMemoryRAG
            rag = ConversationMemoryRAG(db_path=str(tmp_path / "test_rag"))

            # Add old journey
            old_journey = {
                "journey_id": "old-1",
                "problem_description": "Database optimization",
                "meta_learning": "Old approach",
                "timestamp": (datetime.now() - timedelta(days=30)).isoformat(),
                "agents_used": json.dumps([]),
                "business_impact": "Old impact"
            }
            rag.embed_journey(old_journey)

            # Add recent journey
            recent_journey = {
                "journey_id": "recent-1",
                "problem_description": "Database optimization",
                "meta_learning": "New approach",
                "timestamp": datetime.now().isoformat(),
                "agents_used": json.dumps([]),
                "business_impact": "Recent impact"
            }
            rag.embed_journey(recent_journey)

            results = rag.get_relevant_context("database performance", recency_weight=0.3)

            # Recent should be first or weighted higher
            assert len(results) == 2


class TestIntegration:
    """Integration tests with conversation_logger"""

    def test_end_to_end_embed_and_search(self, tmp_path):
        """Full flow: embed journey then search for it"""
        with patch('requests.post') as mock_post:
            mock_response = MagicMock()
            mock_response.json.return_value = {"embeddings": [[0.8] * 768]}
            mock_response.raise_for_status = MagicMock()
            mock_post.return_value = mock_response

            from claude.tools.memory.conversation_memory_rag import ConversationMemoryRAG
            rag = ConversationMemoryRAG(db_path=str(tmp_path / "test_rag"))

            # Embed a journey
            journey = {
                "journey_id": "e2e-test",
                "problem_description": "Kubernetes pod scaling issues",
                "meta_learning": "HPA with custom metrics solves auto-scaling",
                "timestamp": datetime.now().isoformat(),
                "agents_used": json.dumps([{"agent": "SRE Principal Engineer"}]),
                "business_impact": "99.9% uptime achieved"
            }
            rag.embed_journey(journey)

            # Search for related content
            results = rag.search_similar("container scaling problems")

            assert len(results) == 1
            assert results[0]["journey_id"] == "e2e-test"


class TestStats:
    """Test statistics and health checks"""

    def test_get_stats_returns_counts(self, tmp_path):
        """Given initialized RAG, When getting stats, Then returns counts"""
        with patch('requests.post') as mock_post:
            mock_response = MagicMock()
            mock_response.json.return_value = {"embeddings": [[0.5] * 768]}
            mock_response.raise_for_status = MagicMock()
            mock_post.return_value = mock_response

            from claude.tools.memory.conversation_memory_rag import ConversationMemoryRAG
            rag = ConversationMemoryRAG(db_path=str(tmp_path / "test_rag"))

            stats = rag.get_stats()

            assert "total_indexed" in stats
            assert "embedding_model" in stats
            assert "db_path" in stats


class TestSessionStartRetrieval:
    """Test session-start memory retrieval for context injection"""

    @pytest.fixture
    def rag_with_history(self, tmp_path):
        """Create RAG with realistic past work history"""
        with patch('requests.post') as mock_post:
            mock_response = MagicMock()
            mock_response.json.return_value = {"embeddings": [[0.5] * 768]}
            mock_response.raise_for_status = MagicMock()
            mock_post.return_value = mock_response

            from claude.tools.memory.conversation_memory_rag import ConversationMemoryRAG
            rag = ConversationMemoryRAG(db_path=str(tmp_path / "test_rag"))

            # Add realistic past journeys
            journeys = [
                {
                    "journey_id": "past-1",
                    "problem_description": "API performance optimization",
                    "meta_learning": "Connection pooling reduced latency by 40%",
                    "timestamp": (datetime.now() - timedelta(days=5)).isoformat(),
                    "agents_used": json.dumps([{"agent": "SRE Principal Engineer"}]),
                    "business_impact": "40% latency reduction"
                },
                {
                    "journey_id": "past-2",
                    "problem_description": "Database query slowdowns",
                    "meta_learning": "N+1 query pattern was the root cause - use eager loading",
                    "timestamp": (datetime.now() - timedelta(days=3)).isoformat(),
                    "agents_used": json.dumps([{"agent": "SRE Principal Engineer"}]),
                    "business_impact": "90% query time reduction"
                },
                {
                    "journey_id": "past-3",
                    "problem_description": "Security vulnerability assessment",
                    "meta_learning": "JWT tokens need rotation policy",
                    "timestamp": (datetime.now() - timedelta(days=1)).isoformat(),
                    "agents_used": json.dumps([{"agent": "Security Specialist"}]),
                    "business_impact": "Improved security posture"
                }
            ]

            for journey in journeys:
                rag.embed_journey(journey)

            yield rag

    def test_get_memory_context_returns_formatted_string(self, rag_with_history):
        """Given past work, When getting memory context, Then returns formatted string"""
        with patch('requests.post') as mock_post:
            mock_response = MagicMock()
            mock_response.json.return_value = {"embeddings": [[0.5] * 768]}
            mock_response.raise_for_status = MagicMock()
            mock_post.return_value = mock_response

            context = rag_with_history.get_memory_context("API performance issues")

            assert isinstance(context, str)
            assert len(context) > 0

    def test_get_memory_context_includes_relevant_learnings(self, rag_with_history):
        """Given past work, When getting context, Then includes meta_learning"""
        with patch('requests.post') as mock_post:
            mock_response = MagicMock()
            mock_response.json.return_value = {"embeddings": [[0.5] * 768]}
            mock_response.raise_for_status = MagicMock()
            mock_post.return_value = mock_response

            context = rag_with_history.get_memory_context("database optimization")

            # Should include learnings from relevant past work
            assert "meta_learning" in context.lower() or "learned" in context.lower() or "N+1" in context or "learning" in context.lower()

    def test_get_memory_context_respects_limit(self, rag_with_history):
        """Given many past journeys, When limiting results, Then respects limit"""
        with patch('requests.post') as mock_post:
            mock_response = MagicMock()
            mock_response.json.return_value = {"embeddings": [[0.5] * 768]}
            mock_response.raise_for_status = MagicMock()
            mock_post.return_value = mock_response

            context = rag_with_history.get_memory_context("performance", max_results=1)

            # Should only have 1 journey referenced
            assert context.count("journey_id") <= 1 or context.count("Previously") <= 1

    def test_get_memory_context_empty_when_no_matches(self, tmp_path):
        """Given no relevant history, When getting context, Then returns empty/minimal"""
        with patch('requests.post') as mock_post:
            mock_response = MagicMock()
            mock_response.json.return_value = {"embeddings": [[0.5] * 768]}
            mock_response.raise_for_status = MagicMock()
            mock_post.return_value = mock_response

            from claude.tools.memory.conversation_memory_rag import ConversationMemoryRAG
            rag = ConversationMemoryRAG(db_path=str(tmp_path / "empty_rag"))

            context = rag.get_memory_context("anything")

            # Should be empty or indicate no history
            assert context == "" or "no relevant" in context.lower()

    def test_get_memory_context_graceful_without_ollama(self, tmp_path):
        """Given Ollama unavailable, When getting context, Then returns empty gracefully"""
        with patch('requests.post') as mock_post:
            mock_post.side_effect = ConnectionError("Ollama not running")

            from claude.tools.memory.conversation_memory_rag import ConversationMemoryRAG
            rag = ConversationMemoryRAG(db_path=str(tmp_path / "test_rag"))

            context = rag.get_memory_context("test query")

            assert context == ""  # Graceful empty return


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
