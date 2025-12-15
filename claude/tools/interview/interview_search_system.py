#!/usr/bin/env python3
"""
Interview Search System - Hybrid SQLite FTS5 + ChromaDB RAG

Combines structured storage (SQLite with FTS5) with semantic search (ChromaDB)
for comprehensive interview transcript search and analysis.

Features:
- FTS5 full-text search for keyword queries
- ChromaDB RAG for semantic/conceptual queries
- Hybrid search with Reciprocal Rank Fusion (RRF)
- LLM-powered analysis via Ollama

Based on patterns from:
- claude/tools/email_rag_ollama.py (ChromaDB + Ollama)
- claude/tools/database_connection_manager.py (SQLite pooling)

Author: Maia System
Created: 2025-12-15 (Phase 223)
"""

import os
import sys
import json
import uuid
import sqlite3
import requests
from pathlib import Path
from typing import List, Dict, Optional, Any, Tuple
from datetime import datetime
from dataclasses import dataclass, asdict

# Add Maia root to path
MAIA_ROOT = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(MAIA_ROOT))

try:
    import chromadb
    from chromadb.config import Settings
except ImportError:
    print("Missing chromadb. Install: pip3 install chromadb")
    sys.exit(1)

from claude.tools.interview.interview_vtt_parser import InterviewVTTParser, ParsedInterview, VTTSegment


@dataclass
class SearchResult:
    """A single search result"""
    interview_id: str
    candidate_name: str
    role_title: str
    segment_index: int
    speaker: str
    text: str
    score: float
    search_type: str  # fts, semantic, hybrid


@dataclass
class InterviewRecord:
    """Interview metadata record"""
    interview_id: str
    candidate_name: str
    role_title: str
    vtt_file_path: str
    interview_date: Optional[str] = None
    duration_seconds: Optional[int] = None
    total_segments: int = 0
    interviewer_name: str = "Naythan"
    status: str = "active"


class InterviewSearchSystem:
    """
    Hybrid interview search with SQLite FTS5 + ChromaDB RAG.

    Usage:
        system = InterviewSearchSystem()
        system.ingest("/path/to/interview.vtt", "John Smith", "Pod Lead")
        results = system.search("terraform experience", search_type="hybrid")
        answer = system.ask("Which candidate has the strongest Azure experience?")
    """

    # SQL Schema
    SCHEMA = """
    -- Core: Interview metadata
    CREATE TABLE IF NOT EXISTS interviews (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        interview_id TEXT UNIQUE NOT NULL,
        candidate_name TEXT NOT NULL,
        role_title TEXT,
        vtt_file_path TEXT NOT NULL,
        interview_date TEXT,
        duration_seconds INTEGER,
        total_segments INTEGER DEFAULT 0,
        interviewer_name TEXT DEFAULT 'Naythan',
        status TEXT DEFAULT 'active',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    -- Segments: Individual dialogue turns
    CREATE TABLE IF NOT EXISTS interview_segments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        interview_id TEXT NOT NULL,
        segment_index INTEGER NOT NULL,
        speaker TEXT NOT NULL,
        speaker_role TEXT,
        text_content TEXT NOT NULL,
        start_time_ms INTEGER,
        end_time_ms INTEGER,
        word_count INTEGER,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (interview_id) REFERENCES interviews(interview_id) ON DELETE CASCADE,
        UNIQUE(interview_id, segment_index)
    );

    -- Scores: Interview scoring results
    CREATE TABLE IF NOT EXISTS interview_scores (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        interview_id TEXT NOT NULL,
        scoring_framework TEXT NOT NULL,
        total_score REAL NOT NULL,
        max_score REAL NOT NULL,
        percentage REAL NOT NULL,
        score_breakdown TEXT,
        red_flags TEXT,
        green_flags TEXT,
        recommendation TEXT,
        rationale TEXT,
        scored_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (interview_id) REFERENCES interviews(interview_id) ON DELETE CASCADE
    );

    -- Metadata: Flexible key-value storage
    CREATE TABLE IF NOT EXISTS interview_metadata (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        interview_id TEXT NOT NULL,
        key TEXT NOT NULL,
        value TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (interview_id) REFERENCES interviews(interview_id) ON DELETE CASCADE,
        UNIQUE(interview_id, key)
    );

    -- Indexes for performance
    CREATE INDEX IF NOT EXISTS idx_interviews_candidate ON interviews(candidate_name);
    CREATE INDEX IF NOT EXISTS idx_interviews_role ON interviews(role_title);
    CREATE INDEX IF NOT EXISTS idx_interviews_date ON interviews(interview_date);
    CREATE INDEX IF NOT EXISTS idx_interviews_status ON interviews(status);
    CREATE INDEX IF NOT EXISTS idx_segments_interview ON interview_segments(interview_id);
    CREATE INDEX IF NOT EXISTS idx_segments_speaker ON interview_segments(speaker);
    CREATE INDEX IF NOT EXISTS idx_scores_interview ON interview_scores(interview_id);
    CREATE INDEX IF NOT EXISTS idx_scores_recommendation ON interview_scores(recommendation);

    -- FTS5 Virtual Table for full-text search
    CREATE VIRTUAL TABLE IF NOT EXISTS interview_fts USING fts5(
        interview_id,
        candidate_name,
        role_title,
        segment_text,
        tokenize='porter unicode61'
    );

    -- View: Interview summary with aggregated data
    CREATE VIEW IF NOT EXISTS v_interview_summary AS
    SELECT
        i.interview_id,
        i.candidate_name,
        i.role_title,
        i.interview_date,
        i.total_segments,
        i.status,
        COUNT(DISTINCT s.speaker) as speaker_count,
        SUM(s.word_count) as total_words,
        MAX(sc.percentage) as best_score,
        MAX(sc.recommendation) as recommendation
    FROM interviews i
    LEFT JOIN interview_segments s ON i.interview_id = s.interview_id
    LEFT JOIN interview_scores sc ON i.interview_id = sc.interview_id
    GROUP BY i.interview_id;
    """

    # Trigger to sync FTS5 (created separately due to SQLite limitations)
    FTS_TRIGGER = """
    CREATE TRIGGER IF NOT EXISTS interview_segments_fts_insert
    AFTER INSERT ON interview_segments
    BEGIN
        INSERT INTO interview_fts(interview_id, candidate_name, role_title, segment_text)
        SELECT
            NEW.interview_id,
            i.candidate_name,
            i.role_title,
            NEW.text_content
        FROM interviews i WHERE i.interview_id = NEW.interview_id;
    END;
    """

    def __init__(
        self,
        sqlite_path: Optional[str] = None,
        chroma_path: Optional[str] = None,
        embedding_model: str = "nomic-embed-text"
    ):
        """
        Initialize the hybrid search system.

        Args:
            sqlite_path: Path to SQLite database (default: intelligence/interview_search.db)
            chroma_path: Path to ChromaDB store (default: rag_databases/interview_rag)
            embedding_model: Ollama model for embeddings (default: nomic-embed-text)
        """
        # Set paths following Maia conventions
        self.sqlite_path = sqlite_path or os.path.join(
            MAIA_ROOT, "claude", "data", "databases", "intelligence", "interview_search.db"
        )
        self.chroma_path = chroma_path or os.path.join(
            MAIA_ROOT, "claude", "data", "rag_databases", "interview_rag"
        )

        # Ensure directories exist
        os.makedirs(os.path.dirname(self.sqlite_path), exist_ok=True)
        os.makedirs(self.chroma_path, exist_ok=True)

        self.embedding_model = embedding_model
        self.ollama_url = "http://localhost:11434"

        # Initialize parser
        self.parser = InterviewVTTParser()

        # Initialize SQLite
        self._init_sqlite()

        # Initialize ChromaDB
        self._init_chromadb()

        print(f"Interview Search System initialized")
        print(f"  SQLite: {self.sqlite_path}")
        print(f"  ChromaDB: {self.chroma_path}")

    def _init_sqlite(self):
        """Initialize SQLite database with schema"""
        conn = sqlite3.connect(self.sqlite_path)
        conn.row_factory = sqlite3.Row

        # Enable foreign keys and WAL mode
        conn.execute("PRAGMA foreign_keys = ON")
        conn.execute("PRAGMA journal_mode = WAL")

        # Create schema
        conn.executescript(self.SCHEMA)

        # Create FTS trigger (separate due to IF NOT EXISTS limitations)
        try:
            conn.execute(self.FTS_TRIGGER)
        except sqlite3.OperationalError:
            pass  # Trigger already exists

        conn.commit()
        conn.close()

    def _init_chromadb(self):
        """Initialize ChromaDB collection"""
        self.chroma_client = chromadb.PersistentClient(
            path=self.chroma_path,
            settings=Settings(anonymized_telemetry=False)
        )

        self.collection = self.chroma_client.get_or_create_collection(
            name="interview_segments",
            metadata={
                "description": "Interview transcript segments with Ollama embeddings",
                "embedding_model": self.embedding_model,
                "hnsw:space": "cosine"
            }
        )

    def _get_connection(self) -> sqlite3.Connection:
        """Get SQLite connection"""
        conn = sqlite3.connect(self.sqlite_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    def _get_embedding(self, text: str) -> List[float]:
        """Get embedding from Ollama"""
        try:
            response = requests.post(
                f"{self.ollama_url}/api/embed",
                json={"model": self.embedding_model, "input": text},
                timeout=30
            )
            response.raise_for_status()
            return response.json()["embeddings"][0]
        except Exception as e:
            print(f"Embedding error: {e}")
            raise

    # =========================================================================
    # INGESTION
    # =========================================================================

    def ingest(
        self,
        vtt_path: str,
        candidate_name: str,
        role_title: str,
        interview_date: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Ingest a VTT interview file.

        Args:
            vtt_path: Path to VTT file
            candidate_name: Candidate's full name
            role_title: Job role title
            interview_date: Optional date (YYYY-MM-DD)

        Returns:
            Dict with interview_id and stats
        """
        print(f"\nIngesting interview: {candidate_name} - {role_title}")
        print(f"  File: {vtt_path}")

        # Parse VTT
        parsed = self.parser.parse(vtt_path)
        print(f"  Parsed: {parsed.total_segments} segments, {parsed.total_words} words")

        # Generate interview ID
        interview_id = str(uuid.uuid4())

        # Calculate duration
        duration_seconds = None
        if parsed.total_duration_ms:
            duration_seconds = parsed.total_duration_ms // 1000

        # Store in SQLite
        conn = self._get_connection()
        try:
            # Insert interview record
            conn.execute("""
                INSERT INTO interviews
                (interview_id, candidate_name, role_title, vtt_file_path,
                 interview_date, duration_seconds, total_segments, interviewer_name)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                interview_id, candidate_name, role_title, vtt_path,
                interview_date, duration_seconds, parsed.total_segments,
                parsed.interviewer or "Unknown"
            ))

            # Insert segments
            for segment in parsed.segments:
                conn.execute("""
                    INSERT INTO interview_segments
                    (interview_id, segment_index, speaker, speaker_role,
                     text_content, start_time_ms, end_time_ms, word_count)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    interview_id, segment.index, segment.speaker, segment.speaker_role,
                    segment.text, segment.start_time_ms, segment.end_time_ms, segment.word_count
                ))

            conn.commit()
            print(f"  SQLite: Stored {parsed.total_segments} segments")

        finally:
            conn.close()

        # Index in ChromaDB
        print(f"  ChromaDB: Generating embeddings...")
        self._index_segments_to_chromadb(interview_id, candidate_name, role_title, parsed.segments)
        print(f"  ChromaDB: Indexed {len(parsed.segments)} segments")

        return {
            "interview_id": interview_id,
            "candidate_name": candidate_name,
            "role_title": role_title,
            "total_segments": parsed.total_segments,
            "total_words": parsed.total_words,
            "duration_seconds": duration_seconds,
            "status": "success"
        }

    def _index_segments_to_chromadb(
        self,
        interview_id: str,
        candidate_name: str,
        role_title: str,
        segments: List[VTTSegment]
    ):
        """Index interview segments to ChromaDB"""
        documents = []
        metadatas = []
        ids = []
        embeddings = []

        for segment in segments:
            # Create document text (speaker: text format for context)
            doc_text = f"{segment.speaker}: {segment.text}"

            # Generate embedding
            embedding = self._get_embedding(doc_text)

            # Create metadata
            metadata = {
                "interview_id": interview_id,
                "segment_index": segment.index,
                "candidate_name": candidate_name,
                "role_title": role_title,
                "speaker": segment.speaker,
                "speaker_role": segment.speaker_role,
                "word_count": segment.word_count,
            }

            documents.append(doc_text)
            metadatas.append(metadata)
            ids.append(f"{interview_id}_{segment.index}")
            embeddings.append(embedding)

        # Batch insert to ChromaDB
        if documents:
            self.collection.add(
                documents=documents,
                metadatas=metadatas,
                ids=ids,
                embeddings=embeddings
            )

    # =========================================================================
    # SEARCH
    # =========================================================================

    def search(
        self,
        query: str,
        search_type: str = "hybrid",
        n_results: int = 10,
        candidate_filter: Optional[str] = None,
        role_filter: Optional[str] = None
    ) -> List[SearchResult]:
        """
        Search interviews using specified method.

        Args:
            query: Search query
            search_type: 'fts' (keyword), 'semantic', or 'hybrid'
            n_results: Number of results to return
            candidate_filter: Filter by candidate name
            role_filter: Filter by role title

        Returns:
            List of SearchResult objects
        """
        if search_type == "fts":
            return self._fts_search(query, n_results, candidate_filter, role_filter)
        elif search_type == "semantic":
            return self._semantic_search(query, n_results, candidate_filter, role_filter)
        elif search_type == "hybrid":
            return self._hybrid_search(query, n_results, candidate_filter, role_filter)
        else:
            raise ValueError(f"Unknown search type: {search_type}")

    def _sanitize_fts_query(self, query: str) -> str:
        """
        Sanitize query for FTS5 MATCH syntax.

        FTS5 special characters that need escaping: " ' ( ) * : ^ ? -
        """
        # Remove or escape special FTS5 characters
        # Replace apostrophes and quotes with spaces
        sanitized = query.replace("'", " ").replace('"', " ")
        # Remove other special FTS5 operators
        for char in ['(', ')', '*', ':', '^', '?', '-', '+', '~', '<', '>', '[', ']', '{', '}']:
            sanitized = sanitized.replace(char, " ")
        # Collapse multiple spaces
        sanitized = ' '.join(sanitized.split())
        return sanitized

    def _fts_search(
        self,
        query: str,
        limit: int,
        candidate_filter: Optional[str] = None,
        role_filter: Optional[str] = None
    ) -> List[SearchResult]:
        """Full-text search using SQLite FTS5"""
        conn = self._get_connection()
        try:
            # Sanitize query for FTS5
            safe_query = self._sanitize_fts_query(query)
            if not safe_query.strip():
                return []

            # Build query with optional filters
            sql = """
                SELECT
                    f.interview_id,
                    f.candidate_name,
                    f.role_title,
                    f.segment_text,
                    bm25(interview_fts) as score
                FROM interview_fts f
                WHERE interview_fts MATCH ?
            """
            params = [safe_query]

            if candidate_filter:
                sql += " AND f.candidate_name LIKE ?"
                params.append(f"%{candidate_filter}%")

            if role_filter:
                sql += " AND f.role_title LIKE ?"
                params.append(f"%{role_filter}%")

            sql += " ORDER BY score LIMIT ?"
            params.append(limit)

            cursor = conn.execute(sql, params)
            rows = cursor.fetchall()

            results = []
            for row in rows:
                results.append(SearchResult(
                    interview_id=row['interview_id'],
                    candidate_name=row['candidate_name'],
                    role_title=row['role_title'],
                    segment_index=-1,  # FTS doesn't preserve segment index
                    speaker="",
                    text=row['segment_text'],
                    score=abs(row['score']),  # BM25 returns negative scores
                    search_type="fts"
                ))

            return results

        finally:
            conn.close()

    def _semantic_search(
        self,
        query: str,
        limit: int,
        candidate_filter: Optional[str] = None,
        role_filter: Optional[str] = None
    ) -> List[SearchResult]:
        """Semantic search using ChromaDB"""
        # Generate query embedding
        query_embedding = self._get_embedding(query)

        # Build where filter
        where_filter = None
        if candidate_filter or role_filter:
            conditions = []
            if candidate_filter:
                conditions.append({"candidate_name": {"$contains": candidate_filter}})
            if role_filter:
                conditions.append({"role_title": {"$contains": role_filter}})

            if len(conditions) == 1:
                where_filter = conditions[0]
            else:
                where_filter = {"$and": conditions}

        # Query ChromaDB
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=limit,
            where=where_filter if where_filter else None
        )

        search_results = []
        if results['ids'] and results['ids'][0]:
            for i in range(len(results['ids'][0])):
                metadata = results['metadatas'][0][i]
                distance = results['distances'][0][i] if results['distances'] else 0
                relevance = 1 - distance  # Convert distance to similarity

                search_results.append(SearchResult(
                    interview_id=metadata['interview_id'],
                    candidate_name=metadata['candidate_name'],
                    role_title=metadata['role_title'],
                    segment_index=metadata['segment_index'],
                    speaker=metadata['speaker'],
                    text=results['documents'][0][i],
                    score=relevance,
                    search_type="semantic"
                ))

        return search_results

    def _hybrid_search(
        self,
        query: str,
        limit: int,
        candidate_filter: Optional[str] = None,
        role_filter: Optional[str] = None
    ) -> List[SearchResult]:
        """
        Hybrid search combining FTS5 and semantic search using Reciprocal Rank Fusion.
        """
        # Get results from both sources
        fts_results = self._fts_search(query, limit * 2, candidate_filter, role_filter)
        semantic_results = self._semantic_search(query, limit * 2, candidate_filter, role_filter)

        # Reciprocal Rank Fusion
        k = 60  # Standard RRF constant
        scores: Dict[str, float] = {}
        result_map: Dict[str, SearchResult] = {}

        # Score FTS results
        for rank, result in enumerate(fts_results):
            key = f"{result.interview_id}:{result.text[:50]}"
            scores[key] = scores.get(key, 0) + 1 / (k + rank + 1)
            result_map[key] = result

        # Score semantic results
        for rank, result in enumerate(semantic_results):
            key = f"{result.interview_id}:{result.text[:50]}"
            scores[key] = scores.get(key, 0) + 1 / (k + rank + 1)
            if key not in result_map:
                result_map[key] = result

        # Sort by combined score
        sorted_keys = sorted(scores.keys(), key=lambda x: scores[x], reverse=True)

        # Build final results
        results = []
        for key in sorted_keys[:limit]:
            result = result_map[key]
            result.score = scores[key]
            result.search_type = "hybrid"
            results.append(result)

        return results

    # =========================================================================
    # ANALYSIS
    # =========================================================================

    def ask(
        self,
        question: str,
        context_limit: int = 5,
        model: str = "llama3.2"
    ) -> Dict[str, Any]:
        """
        Answer a question using RAG + LLM.

        Args:
            question: The question to answer
            context_limit: Number of context segments to retrieve
            model: Ollama model to use for generation

        Returns:
            Dict with answer, sources, and context
        """
        # Retrieve relevant context
        results = self.search(question, search_type="hybrid", n_results=context_limit)

        if not results:
            return {
                "answer": "No relevant interview content found.",
                "sources": [],
                "context_used": 0
            }

        # Build context
        context_parts = []
        sources = []
        for r in results:
            context_parts.append(f"[{r.candidate_name} - {r.role_title}]\n{r.text}")
            sources.append({
                "candidate": r.candidate_name,
                "role": r.role_title,
                "relevance": r.score
            })

        context = "\n\n---\n\n".join(context_parts)

        # Create prompt
        prompt = f"""Based on the following interview transcript excerpts, answer the question.

INTERVIEW EXCERPTS:
{context}

QUESTION: {question}

Provide a detailed answer based only on the interview content above. If the information is not available in the excerpts, say so.

ANSWER:"""

        # Query Ollama
        try:
            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json={
                    "model": model,
                    "prompt": prompt,
                    "stream": False
                },
                timeout=120
            )
            response.raise_for_status()
            answer = response.json().get("response", "")
        except Exception as e:
            answer = f"Error generating answer: {e}"

        return {
            "answer": answer,
            "sources": sources,
            "context_used": len(results),
            "question": question
        }

    def compare(
        self,
        interview_ids: List[str],
        output_format: str = "table"
    ) -> Dict[str, Any]:
        """
        Compare multiple interviews/candidates.

        Args:
            interview_ids: List of interview IDs to compare
            output_format: 'table', 'json', or 'markdown'

        Returns:
            Comparison data
        """
        conn = self._get_connection()
        try:
            comparisons = []
            for iid in interview_ids:
                # Get interview info
                cursor = conn.execute("""
                    SELECT * FROM v_interview_summary
                    WHERE interview_id = ?
                """, (iid,))
                row = cursor.fetchone()

                if row:
                    comparisons.append(dict(row))

            return {
                "interviews": comparisons,
                "count": len(comparisons),
                "format": output_format
            }

        finally:
            conn.close()

    # =========================================================================
    # LISTING & STATS
    # =========================================================================

    def list_interviews(
        self,
        role_filter: Optional[str] = None,
        status: str = "active"
    ) -> List[Dict[str, Any]]:
        """List all interviews with optional filters"""
        conn = self._get_connection()
        try:
            sql = "SELECT * FROM v_interview_summary WHERE 1=1"
            params = []

            if status:
                sql += " AND status = ?"
                params.append(status)

            if role_filter:
                sql += " AND role_title LIKE ?"
                params.append(f"%{role_filter}%")

            sql += " ORDER BY interview_date DESC"

            cursor = conn.execute(sql, params)
            return [dict(row) for row in cursor.fetchall()]

        finally:
            conn.close()

    def get_stats(self) -> Dict[str, Any]:
        """Get system statistics"""
        conn = self._get_connection()
        try:
            stats = {}

            # Interview count
            cursor = conn.execute("SELECT COUNT(*) as count FROM interviews")
            stats['total_interviews'] = cursor.fetchone()['count']

            # Segment count
            cursor = conn.execute("SELECT COUNT(*) as count FROM interview_segments")
            stats['total_segments'] = cursor.fetchone()['count']

            # Unique candidates
            cursor = conn.execute("SELECT COUNT(DISTINCT candidate_name) as count FROM interviews")
            stats['unique_candidates'] = cursor.fetchone()['count']

            # Unique roles
            cursor = conn.execute("SELECT COUNT(DISTINCT role_title) as count FROM interviews")
            stats['unique_roles'] = cursor.fetchone()['count']

            # ChromaDB count
            stats['chromadb_documents'] = self.collection.count()

            return stats

        finally:
            conn.close()


def main():
    """Basic CLI for testing"""
    import argparse

    parser = argparse.ArgumentParser(description="Interview Search System")
    parser.add_argument('command', choices=['stats', 'list'])

    args = parser.parse_args()

    system = InterviewSearchSystem()

    if args.command == 'stats':
        stats = system.get_stats()
        print("\nInterview Search System Stats:")
        for key, value in stats.items():
            print(f"  {key}: {value}")

    elif args.command == 'list':
        interviews = system.list_interviews()
        print(f"\nFound {len(interviews)} interviews:")
        for i in interviews:
            print(f"  - {i['candidate_name']} ({i['role_title']})")


if __name__ == '__main__':
    main()
