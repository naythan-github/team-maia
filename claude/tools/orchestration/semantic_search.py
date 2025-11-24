#!/usr/bin/env python3
"""
Semantic SYSTEM_STATE Search - Agentic AI Enhancement Phase 3

Implements Agentic RAG pattern for phase history:
  CURRENT: Keyword match -> Load phases
  AGENTIC: Semantic query -> Retrieve relevant phases -> Evaluate -> Refine

Key Features:
- Embed SYSTEM_STATE phases into vector database
- Semantic similarity search
- Agent reasoning about relevant history

Author: Maia System
Created: 2025-11-24 (Agentic AI Enhancement Project - Phase 3)
"""

import json
import math
import re
import sqlite3
import hashlib
from collections import Counter
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass


@dataclass
class PhaseDocument:
    """Represents a phase document"""
    phase_id: int
    title: str
    content: str
    metadata: Dict = None
    embedding: List[float] = None


class SemanticSystemState:
    """
    Semantic Search over SYSTEM_STATE.md phases.

    Uses TF-IDF embeddings by default with optional Ollama integration
    for richer semantic understanding.
    """

    def __init__(
        self,
        db_path: Optional[str] = None,
        use_ollama: bool = False,
        ollama_model: str = "nomic-embed-text"
    ):
        """
        Initialize Semantic Search System.

        Args:
            db_path: Path to SQLite database
            use_ollama: Use Ollama for embeddings (if available)
            ollama_model: Ollama embedding model
        """
        if db_path is None:
            maia_root = Path(__file__).resolve().parents[3]
            db_path = maia_root / "claude" / "data" / "rag_databases" / "system_state_rag"

        self.db_path = Path(db_path)
        self.db_path.mkdir(parents=True, exist_ok=True)
        self.sqlite_path = self.db_path / "semantic_index.db"

        self.use_ollama = use_ollama
        self.ollama_model = ollama_model
        self.ollama_url = "http://localhost:11434"

        # TF-IDF vocabulary (built during indexing)
        self.vocabulary = {}
        self.idf = {}

        self._init_database()
        self._load_vocabulary()

    def _init_database(self):
        """Initialize database schema"""
        conn = sqlite3.connect(self.sqlite_path)
        cursor = conn.cursor()

        # Table 1: Phase Documents
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS phases (
                phase_id INTEGER PRIMARY KEY,
                title TEXT NOT NULL,
                content TEXT NOT NULL,
                metadata_json TEXT,
                embedding_json TEXT,
                content_hash TEXT
            )
        """)

        # Table 2: Vocabulary (for TF-IDF)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS vocabulary (
                term TEXT PRIMARY KEY,
                doc_freq INTEGER DEFAULT 0,
                idf REAL
            )
        """)

        # Index
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_phases_hash
            ON phases(content_hash)
        """)

        conn.commit()
        conn.close()

    def _load_vocabulary(self):
        """Load vocabulary from database"""
        conn = sqlite3.connect(self.sqlite_path)
        cursor = conn.cursor()

        cursor.execute("SELECT term, idf FROM vocabulary")
        for term, idf in cursor.fetchall():
            self.idf[term] = idf

        conn.close()

    def add_phase(
        self,
        phase_id: int,
        title: str,
        content: str,
        metadata: Dict = None
    ):
        """
        Add a phase to the index.

        Args:
            phase_id: Phase number
            title: Phase title
            content: Phase content
            metadata: Optional metadata dict
        """
        full_text = f"{title}\n{content}"
        embedding = self.generate_embedding(full_text)
        content_hash = hashlib.md5(full_text.encode()).hexdigest()

        conn = sqlite3.connect(self.sqlite_path)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT OR REPLACE INTO phases
            (phase_id, title, content, metadata_json, embedding_json, content_hash)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            phase_id,
            title,
            content,
            json.dumps(metadata or {}),
            json.dumps(embedding),
            content_hash
        ))

        # Update vocabulary (using same connection)
        self._update_vocabulary_with_cursor(full_text, cursor)

        conn.commit()
        conn.close()

        # Reload vocabulary
        self._load_vocabulary()

    def _update_vocabulary_with_cursor(self, text: str, cursor):
        """Update vocabulary with terms from text using existing cursor"""
        terms = self._tokenize(text)
        term_counts = Counter(terms)

        for term in term_counts:
            cursor.execute("""
                INSERT INTO vocabulary (term, doc_freq, idf)
                VALUES (?, 1, 0)
                ON CONFLICT(term) DO UPDATE SET
                    doc_freq = doc_freq + 1
            """, (term,))

        # Recalculate IDF values
        cursor.execute("SELECT COUNT(*) FROM phases")
        total_docs = cursor.fetchone()[0] or 1

        cursor.execute("UPDATE vocabulary SET idf = log(? / (doc_freq + 1.0))", (total_docs + 1,))

    def _tokenize(self, text: str) -> List[str]:
        """Tokenize text into terms"""
        # Lowercase and extract words
        text = text.lower()
        words = re.findall(r'\b[a-z][a-z0-9_]+\b', text)

        # Remove common stop words
        stop_words = {'the', 'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been',
                      'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will',
                      'would', 'could', 'should', 'may', 'might', 'must', 'shall',
                      'can', 'need', 'to', 'of', 'in', 'for', 'on', 'with', 'at',
                      'by', 'from', 'as', 'into', 'through', 'during', 'before',
                      'after', 'above', 'below', 'between', 'under', 'again',
                      'further', 'then', 'once', 'here', 'there', 'when', 'where',
                      'why', 'how', 'all', 'each', 'few', 'more', 'most', 'other',
                      'some', 'such', 'no', 'nor', 'not', 'only', 'own', 'same',
                      'so', 'than', 'too', 'very', 'just', 'and', 'but', 'if', 'or',
                      'because', 'until', 'while', 'this', 'that', 'these', 'those'}

        return [w for w in words if w not in stop_words and len(w) > 2]

    def generate_embedding(self, text: str) -> List[float]:
        """
        Generate embedding for text.

        Uses TF-IDF by default, Ollama if enabled.

        Args:
            text: Text to embed

        Returns:
            Embedding vector
        """
        if self.use_ollama:
            try:
                return self._ollama_embedding(text)
            except Exception:
                pass  # Fall back to TF-IDF

        return self._tfidf_embedding(text)

    def _tfidf_embedding(self, text: str) -> List[float]:
        """Generate TF-IDF based embedding"""
        terms = self._tokenize(text)
        term_freq = Counter(terms)

        # Create sparse vector representation as dict
        vector = {}
        for term, count in term_freq.items():
            tf = 1 + math.log(count) if count > 0 else 0
            idf = self.idf.get(term, 1.0)
            vector[term] = tf * idf

        # Normalize
        magnitude = math.sqrt(sum(v * v for v in vector.values())) or 1
        return {k: v / magnitude for k, v in vector.items()}

    def _ollama_embedding(self, text: str) -> List[float]:
        """Generate embedding using Ollama"""
        import requests

        response = requests.post(
            f"{self.ollama_url}/api/embeddings",
            json={"model": self.ollama_model, "prompt": text},
            timeout=30
        )
        response.raise_for_status()
        return response.json().get("embedding", [])

    def calculate_similarity(
        self,
        emb1: Any,
        emb2: Any
    ) -> float:
        """
        Calculate cosine similarity between embeddings.

        Args:
            emb1: First embedding (dict or list)
            emb2: Second embedding (dict or list)

        Returns:
            Similarity score (0.0-1.0)
        """
        # Handle dict (TF-IDF) embeddings
        if isinstance(emb1, dict) and isinstance(emb2, dict):
            # Sparse dot product
            common_keys = set(emb1.keys()) & set(emb2.keys())
            dot = sum(emb1[k] * emb2[k] for k in common_keys)
            return dot  # Already normalized

        # Handle list (Ollama) embeddings
        if isinstance(emb1, list) and isinstance(emb2, list):
            dot = sum(a * b for a, b in zip(emb1, emb2))
            mag1 = math.sqrt(sum(a * a for a in emb1)) or 1
            mag2 = math.sqrt(sum(b * b for b in emb2)) or 1
            return dot / (mag1 * mag2)

        return 0.0

    def search(
        self,
        query: str,
        limit: int = 10,
        filter_metadata: Dict = None
    ) -> List[Dict]:
        """
        Search for relevant phases.

        Args:
            query: Search query
            limit: Maximum results
            filter_metadata: Optional metadata filter

        Returns:
            List of matching phases with relevance scores
        """
        query_embedding = self.generate_embedding(query)

        conn = sqlite3.connect(self.sqlite_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT phase_id, title, content, metadata_json, embedding_json
            FROM phases
        """)

        results = []
        for row in cursor.fetchall():
            phase_id, title, content, meta_json, emb_json = row
            metadata = json.loads(meta_json) if meta_json else {}

            # Apply metadata filter
            if filter_metadata:
                match = all(metadata.get(k) == v for k, v in filter_metadata.items())
                if not match:
                    continue

            # Calculate similarity
            try:
                stored_emb = json.loads(emb_json) if emb_json else {}
                relevance = self.calculate_similarity(query_embedding, stored_emb)
            except Exception:
                relevance = 0.0

            results.append({
                'phase_id': phase_id,
                'title': title,
                'content': content[:500],
                'metadata': metadata,
                'relevance': relevance
            })

        conn.close()

        # Sort by relevance
        results.sort(key=lambda x: x['relevance'], reverse=True)
        return results[:limit]

    def update_phase(self, phase_id: int, title: str, content: str, metadata: Dict = None):
        """Update an existing phase"""
        self.add_phase(phase_id, title, content, metadata)

    def delete_phase(self, phase_id: int):
        """Delete a phase from the index"""
        conn = sqlite3.connect(self.sqlite_path)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM phases WHERE phase_id = ?", (phase_id,))
        conn.commit()
        conn.close()

    def get_phase_count(self) -> int:
        """Get number of indexed phases"""
        conn = sqlite3.connect(self.sqlite_path)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM phases")
        count = cursor.fetchone()[0]
        conn.close()
        return count

    def bulk_index(self, phases: List[Dict]):
        """Bulk index multiple phases"""
        for phase in phases:
            self.add_phase(
                phase_id=phase['phase_id'],
                title=phase['title'],
                content=phase['content'],
                metadata=phase.get('metadata')
            )

    def get_similar_phases(self, phase_id: int, limit: int = 5) -> List[Dict]:
        """Find phases similar to a given phase"""
        conn = sqlite3.connect(self.sqlite_path)
        cursor = conn.cursor()

        # Get source phase
        cursor.execute("""
            SELECT title, content, embedding_json FROM phases WHERE phase_id = ?
        """, (phase_id,))

        row = cursor.fetchone()
        conn.close()

        if not row:
            return []

        title, content, emb_json = row
        source_emb = json.loads(emb_json) if emb_json else self.generate_embedding(f"{title}\n{content}")

        # Search excluding source
        results = self.search(f"{title} {content}", limit=limit + 1)
        return [r for r in results if r['phase_id'] != phase_id][:limit]

    def parse_system_state(self, content: str) -> List[Dict]:
        """
        Parse SYSTEM_STATE.md format into phase dicts.

        Args:
            content: Raw markdown content

        Returns:
            List of phase dicts
        """
        phases = []

        # Pattern: ## Phase N: Title
        pattern = r'##\s+Phase\s+(\d+):\s+(.+?)(?=\n##\s+Phase|\Z)'
        matches = re.findall(pattern, content, re.DOTALL)

        for match in matches:
            phase_id = int(match[0])
            rest = match[1].strip()

            # Split title from content
            lines = rest.split('\n', 1)
            title = lines[0].strip()
            content = lines[1].strip() if len(lines) > 1 else ""

            phases.append({
                'phase_id': phase_id,
                'title': f"Phase {phase_id}: {title}",
                'content': content
            })

        return phases


def main():
    """CLI for semantic search"""
    import argparse

    parser = argparse.ArgumentParser(description="Semantic SYSTEM_STATE Search")
    subparsers = parser.add_subparsers(dest='command', help='Commands')

    # Search command
    search_parser = subparsers.add_parser('search', help='Search phases')
    search_parser.add_argument('query', help='Search query')
    search_parser.add_argument('--limit', '-n', type=int, default=5)

    # Index command
    index_parser = subparsers.add_parser('index', help='Index SYSTEM_STATE.md')
    index_parser.add_argument('--file', '-f', help='Path to SYSTEM_STATE.md')

    # Stats command
    subparsers.add_parser('stats', help='Show index statistics')

    args = parser.parse_args()

    search = SemanticSystemState()

    if args.command == 'search':
        results = search.search(args.query, limit=args.limit)
        print(f"\nSearch: {args.query}")
        print("=" * 50)
        for r in results:
            print(f"\n[{r['relevance']:.0%}] {r['title']}")
            print(f"   {r['content'][:100]}...")

    elif args.command == 'index':
        if args.file:
            with open(args.file, 'r') as f:
                content = f.read()
            phases = search.parse_system_state(content)
            search.bulk_index(phases)
            print(f"Indexed {len(phases)} phases")
        else:
            print("Provide --file")

    elif args.command == 'stats':
        count = search.get_phase_count()
        print(f"\nSemantic Search Index")
        print("=" * 40)
        print(f"Indexed Phases: {count}")
        print(f"Vocabulary Size: {len(search.idf)}")

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
