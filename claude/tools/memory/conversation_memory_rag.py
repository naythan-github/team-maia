#!/usr/bin/env python3
"""
Conversation Memory RAG System

Hybrid memory system using ChromaDB for semantic search on conversation journeys.
Works alongside conversations.db (SQLite) to enable cross-session learning.

Uses Ollama's nomic-embed-text for 100% local embeddings (same as email_rag).

Author: SRE Principal Engineer Agent
Created: 2025-12-08
"""

import os
import sys
import json
import logging
import requests
from pathlib import Path
from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

MAIA_ROOT = Path(__file__).parent.parent.parent.parent

try:
    import chromadb
    from chromadb.config import Settings
except ImportError:
    logger.error("Missing chromadb. Install: pip3 install chromadb")
    chromadb = None


class ConversationMemoryRAG:
    """
    Conversation Memory RAG with Ollama local embeddings.

    Provides semantic search over past conversation journeys to enable
    cross-session memory and context retrieval.

    Features:
    - Local embeddings (Ollama nomic-embed-text)
    - ChromaDB vector storage
    - Semantic similarity search
    - Recency weighting
    - Graceful degradation
    """

    DEFAULT_DB_PATH = MAIA_ROOT / "claude" / "data" / "rag_databases" / "conversation_memory_rag"
    EMBEDDING_MODEL = "nomic-embed-text"
    OLLAMA_URL = "http://localhost:11434"

    def __init__(self, db_path: Optional[str] = None):
        """
        Initialize Conversation Memory RAG.

        Args:
            db_path: Optional custom database path (defaults to UFC-compliant location)
        """
        self.db_path = Path(db_path) if db_path else self.DEFAULT_DB_PATH
        self.db_path.mkdir(parents=True, exist_ok=True)

        # Index state tracking (avoid re-embedding)
        self.index_state_file = self.db_path / "index_state.json"
        self.index_state = self._load_index_state()

        # Initialize ChromaDB
        if chromadb is None:
            logger.warning("ChromaDB not available - running in degraded mode")
            self.client = None
            self.collection = None
        else:
            try:
                self.client = chromadb.PersistentClient(
                    path=str(self.db_path),
                    settings=Settings(anonymized_telemetry=False)
                )
                self.collection = self.client.get_or_create_collection(
                    name="conversation_memory",
                    metadata={"description": "Conversation journey embeddings for cross-session memory"}
                )
                logger.info(f"Conversation Memory RAG initialized at {self.db_path}")
            except Exception as e:
                logger.error(f"Failed to initialize ChromaDB: {e}")
                self.client = None
                self.collection = None

    def _load_index_state(self) -> Dict[str, Any]:
        """Load index state from file."""
        if self.index_state_file.exists():
            try:
                with open(self.index_state_file, 'r') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError) as e:
                logger.warning(f"Failed to load index state: {e}")
        return {"indexed_journeys": {}, "last_sync_time": None}

    def _save_index_state(self) -> None:
        """Save index state to file."""
        try:
            with open(self.index_state_file, 'w') as f:
                json.dump(self.index_state, f, indent=2)
        except IOError as e:
            logger.error(f"Failed to save index state: {e}")

    def _get_embedding(self, text: str) -> Optional[List[float]]:
        """
        Get embedding from Ollama.

        Args:
            text: Text to embed

        Returns:
            Embedding vector or None if unavailable
        """
        try:
            response = requests.post(
                f"{self.OLLAMA_URL}/api/embed",
                json={"model": self.EMBEDDING_MODEL, "input": text},
                timeout=30
            )
            response.raise_for_status()
            return response.json()["embeddings"][0]
        except requests.exceptions.ConnectionError:
            logger.warning("Ollama not available - cannot generate embedding")
            return None
        except Exception as e:
            logger.error(f"Embedding generation failed: {e}")
            return None

    def embed_journey(self, journey_data: Dict[str, Any], force: bool = False) -> bool:
        """
        Generate embedding for a journey and store in ChromaDB.

        Args:
            journey_data: Journey dict with journey_id, problem_description, meta_learning, etc.
            force: Re-embed even if already indexed

        Returns:
            True if successful, False otherwise
        """
        if self.collection is None:
            logger.warning("ChromaDB not available - skipping embedding")
            return False

        journey_id = journey_data.get("journey_id")
        if not journey_id:
            logger.error("Journey data missing journey_id")
            return False

        # Check if already indexed
        if not force and journey_id in self.index_state["indexed_journeys"]:
            logger.debug(f"Journey {journey_id} already indexed - skipping")
            return True

        # Build text for embedding (problem + learning = most valuable)
        problem = journey_data.get("problem_description", "")
        learning = journey_data.get("meta_learning", "")
        embed_text = f"{problem}\n\n{learning}"

        if not embed_text.strip():
            logger.warning(f"Journey {journey_id} has no content to embed")
            return False

        # Generate embedding
        embedding = self._get_embedding(embed_text)
        if embedding is None:
            return False

        # Prepare metadata
        metadata = {
            "journey_id": journey_id,
            "timestamp": journey_data.get("timestamp", datetime.now().isoformat()),
            "problem_description": problem[:500] if problem else "",
            "meta_learning": learning[:500] if learning else "",
            "agents_used": journey_data.get("agents_used", "[]"),
            "business_impact": journey_data.get("business_impact", "")[:200]
        }

        try:
            # Store in ChromaDB
            self.collection.add(
                documents=[embed_text],
                embeddings=[embedding],
                metadatas=[metadata],
                ids=[journey_id]
            )

            # Update index state
            self.index_state["indexed_journeys"][journey_id] = datetime.now().isoformat()
            self._save_index_state()

            logger.info(f"Embedded journey {journey_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to store embedding: {e}")
            return False

    def search_similar(
        self,
        query: str,
        n_results: int = 5,
        min_relevance: float = 0.0
    ) -> List[Dict[str, Any]]:
        """
        Semantic search for similar past journeys.

        Args:
            query: Search query
            n_results: Maximum results to return
            min_relevance: Minimum relevance score (0-1)

        Returns:
            List of matching journeys with relevance scores
        """
        if self.collection is None:
            logger.warning("ChromaDB not available - returning empty results")
            return []

        # Generate query embedding
        query_embedding = self._get_embedding(query)
        if query_embedding is None:
            return []

        try:
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=n_results
            )

            matches = []
            for i in range(len(results['ids'][0])):
                relevance = 1 - results['distances'][0][i]  # Convert distance to similarity

                if relevance < min_relevance:
                    continue

                metadata = results['metadatas'][0][i]
                matches.append({
                    "journey_id": metadata.get("journey_id"),
                    "problem_description": metadata.get("problem_description"),
                    "meta_learning": metadata.get("meta_learning"),
                    "timestamp": metadata.get("timestamp"),
                    "agents_used": metadata.get("agents_used"),
                    "business_impact": metadata.get("business_impact"),
                    "relevance": relevance,
                    "content": results['documents'][0][i]
                })

            return matches

        except Exception as e:
            logger.error(f"Search failed: {e}")
            return []

    def get_relevant_context(
        self,
        current_problem: str,
        n_results: int = 3,
        recency_weight: float = 0.2
    ) -> List[Dict[str, Any]]:
        """
        Get relevant past context for session start.

        Combines semantic similarity with recency weighting.

        Args:
            current_problem: Current session's problem/query
            n_results: Number of results
            recency_weight: How much to weight recency (0-1)

        Returns:
            List of relevant journeys, weighted by relevance and recency
        """
        # Get more results than needed for re-ranking
        candidates = self.search_similar(current_problem, n_results=n_results * 2)

        if not candidates:
            return []

        # Apply recency weighting
        now = datetime.now()
        for candidate in candidates:
            try:
                timestamp = datetime.fromisoformat(candidate.get("timestamp", ""))
                days_old = (now - timestamp).days
                # Decay factor: recent = 1.0, 30 days old = 0.5, 90 days = 0.25
                recency_score = 1.0 / (1.0 + days_old / 30.0)
            except (ValueError, TypeError):
                recency_score = 0.5  # Default for unparseable dates

            # Combined score
            semantic_score = candidate.get("relevance", 0)
            candidate["combined_score"] = (
                (1 - recency_weight) * semantic_score +
                recency_weight * recency_score
            )

        # Sort by combined score
        candidates.sort(key=lambda x: x.get("combined_score", 0), reverse=True)

        return candidates[:n_results]

    def sync_from_sqlite(
        self,
        journeys: List[Dict[str, Any]],
        force: bool = False
    ) -> Dict[str, int]:
        """
        Sync journeys from SQLite to ChromaDB.

        Args:
            journeys: List of journey dicts from conversations.db
            force: Re-embed all (ignore index state)

        Returns:
            Stats dict with indexed/skipped counts
        """
        stats = {"indexed": 0, "skipped": 0, "errors": 0}

        for journey in journeys:
            journey_id = journey.get("journey_id")

            if not force and journey_id in self.index_state["indexed_journeys"]:
                stats["skipped"] += 1
                continue

            if self.embed_journey(journey, force=force):
                stats["indexed"] += 1
            else:
                stats["errors"] += 1

        self.index_state["last_sync_time"] = datetime.now().isoformat()
        self._save_index_state()

        logger.info(f"Sync complete: {stats}")
        return stats

    def get_stats(self) -> Dict[str, Any]:
        """Get system statistics."""
        return {
            "total_indexed": len(self.index_state.get("indexed_journeys", {})),
            "last_sync_time": self.index_state.get("last_sync_time"),
            "collection_count": self.collection.count() if self.collection else 0,
            "embedding_model": self.EMBEDDING_MODEL,
            "db_path": str(self.db_path),
            "chromadb_available": self.collection is not None
        }

    def get_memory_context(
        self,
        current_query: str,
        max_results: int = 3,
        min_relevance: float = 0.3
    ) -> str:
        """
        Get formatted memory context for session-start injection.

        Retrieves relevant past work and formats it for context injection
        at the start of a new session.

        Args:
            current_query: Current session's problem/question
            max_results: Maximum number of past journeys to include
            min_relevance: Minimum relevance threshold (0-1)

        Returns:
            Formatted string for context injection, or empty string if none
        """
        if self.collection is None or self.collection.count() == 0:
            return ""

        try:
            # Get relevant context with recency weighting
            results = self.get_relevant_context(
                current_query,
                n_results=max_results,
                recency_weight=0.2
            )

            if not results:
                return ""

            # Filter by minimum relevance
            relevant = [r for r in results if r.get("relevance", 0) >= min_relevance]

            if not relevant:
                return ""

            # Format as readable context
            lines = ["## Relevant Past Work\n"]

            for i, journey in enumerate(relevant, 1):
                timestamp = journey.get("timestamp", "")
                try:
                    # Parse and format date nicely
                    dt = datetime.fromisoformat(timestamp)
                    date_str = dt.strftime("%b %d")
                except (ValueError, TypeError):
                    date_str = "Recent"

                problem = journey.get("problem_description", "Unknown")[:80]
                learning = journey.get("meta_learning", "")[:150]
                relevance = journey.get("relevance", 0)
                agents = journey.get("agents_used", "[]")

                # Parse agents if JSON string
                if isinstance(agents, str):
                    try:
                        import json
                        agents_list = json.loads(agents)
                        agent_names = [a.get("agent", "") for a in agents_list if isinstance(a, dict)]
                        agent_str = ", ".join(agent_names) if agent_names else "Unknown"
                    except (json.JSONDecodeError, TypeError):
                        agent_str = "Unknown"
                else:
                    agent_str = "Unknown"

                lines.append(f"### [{date_str}] {problem}")
                lines.append(f"- **Agent**: {agent_str}")
                lines.append(f"- **Learning**: {learning}")
                lines.append(f"- **Relevance**: {relevance:.0%}")
                lines.append("")

            return "\n".join(lines)

        except Exception as e:
            logger.warning(f"Memory context retrieval failed: {e}")
            return ""


def main():
    """CLI interface for Conversation Memory RAG."""
    import sys

    print("🧠 Conversation Memory RAG System\n")

    rag = ConversationMemoryRAG()

    if len(sys.argv) < 2:
        print("Usage: conversation_memory_rag.py <command> [args...]")
        print("\nCommands:")
        print("  stats              - Show system statistics")
        print("  search <query>     - Search for similar journeys")
        print("  sync               - Sync from conversations.db")
        print("\nStats:")
        stats = rag.get_stats()
        for key, value in stats.items():
            print(f"  {key}: {value}")
        return 0

    command = sys.argv[1]

    if command == "stats":
        stats = rag.get_stats()
        print("📊 System Statistics:")
        for key, value in stats.items():
            print(f"  {key}: {value}")

    elif command == "search":
        if len(sys.argv) < 3:
            print("Usage: conversation_memory_rag.py search <query>")
            return 1
        query = " ".join(sys.argv[2:])
        print(f"🔍 Searching for: {query}\n")
        results = rag.search_similar(query)
        if not results:
            print("No matching journeys found.")
        else:
            for i, r in enumerate(results, 1):
                print(f"{i}. [{r['relevance']:.1%}] {r['problem_description'][:60]}...")
                print(f"   Learning: {r['meta_learning'][:80]}...")
                print()

    elif command == "sync":
        print("🔄 Syncing from conversations.db...")
        # Import and use conversation logger
        try:
            sys.path.insert(0, str(MAIA_ROOT))
            from claude.tools.conversation_logger import ConversationLogger

            logger_instance = ConversationLogger()
            journeys = logger_instance.get_week_journeys(include_private=True)

            # Convert to expected format
            journey_list = []
            for j in journeys:
                journey_list.append({
                    "journey_id": j.get("journey_id"),
                    "problem_description": j.get("problem_description"),
                    "meta_learning": j.get("meta_learning"),
                    "timestamp": j.get("timestamp"),
                    "agents_used": json.dumps(j.get("agents_used", [])) if isinstance(j.get("agents_used"), list) else j.get("agents_used", "[]"),
                    "business_impact": j.get("business_impact")
                })

            stats = rag.sync_from_sqlite(journey_list)
            print(f"✅ Sync complete: {stats}")
        except ImportError as e:
            print(f"❌ Could not import ConversationLogger: {e}")
            return 1

    else:
        print(f"Unknown command: {command}")
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
