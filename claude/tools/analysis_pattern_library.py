#!/usr/bin/env python3
"""
Analysis Pattern Library - Global Analytical Pattern Storage and Retrieval

Stores proven analytical approaches (SQL queries, presentation formats, business context)
for reuse across conversations and agents. Enables institutional analytical memory.

Phase 141: Global Analysis Pattern Library
TDD Implementation - Minimal code to pass tests (GREEN phase)
"""

import sqlite3
import json
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import logging

# Try to import ChromaDB (optional dependency)
try:
    import chromadb
    CHROMADB_AVAILABLE = True
except ImportError:
    CHROMADB_AVAILABLE = False

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ValidationError(Exception):
    """Raised when pattern validation fails."""
    pass


class PatternNotFoundError(Exception):
    """Raised when pattern doesn't exist."""
    pass


class AnalysisPatternLibrary:
    """
    Global analysis pattern storage and retrieval system.

    Minimal implementation to pass TDD tests.
    """

    def __init__(self, db_path: str = None, chromadb_path: str = None):
        """Initialize with temp databases."""
        if db_path is None:
            maia_root = Path(__file__).parent.parent.parent
            db_path = maia_root / "claude" / "data" / "analysis_patterns.db"

        if chromadb_path is None:
            maia_root = Path(__file__).parent.parent.parent
            chromadb_path = maia_root / "claude" / "data" / "rag_databases" / "analysis_patterns"

        self.db_path = str(db_path)
        self.chromadb_path = str(chromadb_path)

        # Ensure directories exist
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        Path(self.chromadb_path).mkdir(parents=True, exist_ok=True)

        self._init_sqlite()
        self._init_chromadb()

    def _init_sqlite(self):
        """Initialize SQLite schema."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("PRAGMA journal_mode=WAL")

        # Create tables
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS analysis_patterns (
                pattern_id TEXT PRIMARY KEY,
                pattern_name TEXT NOT NULL,
                domain TEXT NOT NULL,
                question_type TEXT NOT NULL,
                description TEXT NOT NULL,
                sql_template TEXT,
                presentation_format TEXT,
                business_context TEXT,
                example_input TEXT,
                example_output TEXT,
                created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                created_by TEXT,
                version INTEGER DEFAULT 1,
                status TEXT DEFAULT 'active',
                tags TEXT
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS pattern_usage (
                usage_id INTEGER PRIMARY KEY AUTOINCREMENT,
                pattern_id TEXT NOT NULL,
                used_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                user_question TEXT,
                success BOOLEAN,
                feedback TEXT,
                FOREIGN KEY (pattern_id) REFERENCES analysis_patterns(pattern_id)
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS pattern_versions (
                version_id INTEGER PRIMARY KEY AUTOINCREMENT,
                pattern_id TEXT NOT NULL,
                version INTEGER NOT NULL,
                changes TEXT,
                previous_version_id TEXT,
                created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (pattern_id) REFERENCES analysis_patterns(pattern_id)
            )
        """)

        # Create indexes
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_patterns_domain ON analysis_patterns(domain)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_patterns_status ON analysis_patterns(status)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_usage_pattern ON pattern_usage(pattern_id)")

        conn.commit()
        conn.close()

    def _init_chromadb(self):
        """Initialize ChromaDB (optional)."""
        if not CHROMADB_AVAILABLE:
            self.chroma_client = None
            self.chroma_collection = None
            return

        try:
            self.chroma_client = chromadb.PersistentClient(path=self.chromadb_path)
            self.chroma_collection = self.chroma_client.get_or_create_collection(
                name="analysis_patterns_embeddings"
            )
        except Exception as e:
            logger.warning(f"ChromaDB initialization failed: {e}")
            self.chroma_client = None
            self.chroma_collection = None

    def save_pattern(self,
                     pattern_name: str,
                     domain: str,
                     question_type: str,
                     description: str,
                     sql_template: str = None,
                     presentation_format: str = None,
                     business_context: str = None,
                     example_input: str = None,
                     example_output: str = None,
                     tags: List[str] = None,
                     created_by: str = None) -> str:
        """
        Save a new analysis pattern.

        Returns:
            pattern_id: Auto-generated unique ID
        """
        # Validate required fields
        if not pattern_name:
            raise ValidationError("Missing required field: pattern_name")
        if not domain:
            raise ValidationError("Missing required field: domain")
        if not question_type:
            raise ValidationError("Missing required field: question_type")
        if not description:
            raise ValidationError("Missing required field: description")

        # Generate pattern ID
        timestamp = int(time.time() * 1000)
        pattern_id = f"{domain}_{question_type}_{timestamp}".lower().replace(' ', '_')

        # Prepare data
        tags_json = json.dumps(tags) if tags else None

        # Save to database
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO analysis_patterns (
                pattern_id, pattern_name, domain, question_type, description,
                sql_template, presentation_format, business_context,
                example_input, example_output, tags, created_by,
                created_date, version, status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, [
            pattern_id, pattern_name, domain, question_type, description,
            sql_template, presentation_format, business_context,
            example_input, example_output, tags_json, created_by,
            datetime.now().isoformat(), 1, 'active'
        ])

        conn.commit()
        conn.close()

        # Create ChromaDB embedding if available
        if self.chroma_collection:
            try:
                embed_text = f"{description} {example_input or ''}"
                if tags:
                    embed_text += " " + " ".join(tags)

                self.chroma_collection.add(
                    documents=[embed_text],
                    ids=[pattern_id],
                    metadatas=[{"domain": domain, "pattern_name": pattern_name}]
                )
            except Exception as e:
                logger.warning(f"ChromaDB embedding failed: {e}")

        return pattern_id

    def get_pattern(self, pattern_id: str, include_archived: bool = False) -> Optional[Dict[str, Any]]:
        """
        Retrieve pattern by ID.

        Returns:
            Pattern dictionary or None if not found
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        query = "SELECT * FROM analysis_patterns WHERE pattern_id = ?"
        if not include_archived:
            query += " AND status != 'archived'"

        cursor.execute(query, [pattern_id])
        row = cursor.fetchone()

        if not row:
            conn.close()
            return None

        # Convert to dict
        pattern = dict(row)

        # Parse tags
        if pattern.get('tags'):
            try:
                pattern['tags'] = json.loads(pattern['tags'])
            except json.JSONDecodeError:
                pattern['tags'] = []

        # Add usage statistics
        cursor.execute("""
            SELECT
                COUNT(*) as total_uses,
                SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) as successful_uses,
                MAX(used_date) as last_used
            FROM pattern_usage
            WHERE pattern_id = ?
        """, [pattern_id])

        usage_row = cursor.fetchone()
        total_uses = usage_row[0] if usage_row[0] else 0
        successful_uses = usage_row[1] if usage_row[1] else 0
        last_used = usage_row[2]

        success_rate = (successful_uses / total_uses) if total_uses > 0 else None

        pattern['usage_stats'] = {
            'total_uses': total_uses,
            'success_rate': success_rate,
            'last_used': last_used
        }

        conn.close()
        return pattern

    def list_patterns(self,
                     domain: str = None,
                     status: str = 'active',
                     limit: int = 50) -> List[Dict[str, Any]]:
        """List all patterns (optionally filtered)."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        where_clauses = []
        params = []

        if status:
            where_clauses.append("status = ?")
            params.append(status)

        if domain:
            where_clauses.append("domain = ?")
            params.append(domain)

        where_sql = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""

        query = f"SELECT * FROM analysis_patterns {where_sql} LIMIT ?"
        params.append(limit)

        cursor.execute(query, params)
        rows = cursor.fetchall()

        patterns = []
        for row in rows:
            pattern = dict(row)
            if pattern.get('tags'):
                try:
                    pattern['tags'] = json.loads(pattern['tags'])
                except json.JSONDecodeError:
                    pattern['tags'] = []
            patterns.append(pattern)

        conn.close()
        return patterns

    def search_patterns(self,
                       query: str,
                       domain: str = None,
                       limit: int = 5,
                       similarity_threshold: float = 0.75) -> List[Tuple[Dict[str, Any], float]]:
        """
        Semantic search for matching patterns.

        Returns:
            List of (pattern_dict, similarity_score) tuples
        """
        # Try ChromaDB first
        if self.chroma_collection:
            try:
                # ChromaDB query - no where filter for now (causes issues)
                results = self.chroma_collection.query(
                    query_texts=[query],
                    n_results=limit * 2
                )

                if results['ids'] and results['ids'][0]:
                    pattern_results = []
                    for idx, pattern_id in enumerate(results['ids'][0]):
                        distance = results['distances'][0][idx]
                        # ChromaDB distance is already 0-1 where lower is better
                        # Convert to similarity (higher is better)
                        similarity = max(0, 1 - distance)

                        pattern = self.get_pattern(pattern_id)
                        if pattern:
                            # Apply domain filter manually if specified
                            if domain and pattern.get('domain') != domain:
                                continue

                            if similarity >= similarity_threshold:
                                pattern_results.append((pattern, similarity))

                    pattern_results.sort(key=lambda x: x[1], reverse=True)
                    if pattern_results:
                        return pattern_results[:limit]
            except Exception as e:
                logger.warning(f"ChromaDB search failed: {e}")

        # Fallback to SQLite
        return self._sqlite_search(query, domain, limit)

    def _sqlite_search(self, query: str, domain: str, limit: int) -> List[Tuple[Dict[str, Any], float]]:
        """SQLite fallback search."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        where_clauses = ["status = 'active'"]
        params = []

        if query:
            where_clauses.append("(description LIKE ? OR pattern_name LIKE ?)")
            search_term = f"%{query}%"
            params.extend([search_term, search_term])

        if domain:
            where_clauses.append("domain = ?")
            params.append(domain)

        sql = f"SELECT * FROM analysis_patterns WHERE {' AND '.join(where_clauses)} LIMIT ?"
        params.append(limit)

        cursor.execute(sql, params)
        rows = cursor.fetchall()

        results = []
        for row in rows:
            pattern = dict(row)
            if pattern.get('tags'):
                try:
                    pattern['tags'] = json.loads(pattern['tags'])
                except json.JSONDecodeError:
                    pattern['tags'] = []
            # Higher default similarity for SQLite matches (they matched LIKE)
            results.append((pattern, 0.80))  # Default similarity for SQLite

        conn.close()
        return results

    def update_pattern(self,
                      pattern_id: str,
                      changes: str = None,
                      **kwargs) -> str:
        """
        Update pattern (creates new version).

        Args:
            pattern_id: Existing pattern ID
            changes: Description of changes
            **kwargs: Fields to update

        Returns:
            new_pattern_id: New version ID
        """
        # Get existing pattern
        old_pattern = self.get_pattern(pattern_id, include_archived=True)
        if not old_pattern:
            raise PatternNotFoundError(f"Pattern not found: {pattern_id}")

        # Create new version
        new_version = old_pattern['version'] + 1

        # Generate new pattern ID with version
        base_id = pattern_id.rsplit('_', 1)[0]  # Remove timestamp
        new_pattern_id = f"{base_id}_v{new_version}_{int(time.time() * 1000)}"

        # Merge old data with updates
        new_data = {
            'pattern_name': old_pattern['pattern_name'],
            'domain': old_pattern['domain'],
            'question_type': old_pattern['question_type'],
            'description': old_pattern['description'],
            'sql_template': old_pattern.get('sql_template'),
            'presentation_format': old_pattern.get('presentation_format'),
            'business_context': old_pattern.get('business_context'),
            'example_input': old_pattern.get('example_input'),
            'example_output': old_pattern.get('example_output'),
            'tags': old_pattern.get('tags'),
            'created_by': old_pattern.get('created_by')
        }

        # Apply updates
        for key, value in kwargs.items():
            if key in new_data:
                new_data[key] = value

        # Save new version
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        tags_json = json.dumps(new_data['tags']) if new_data['tags'] else None

        cursor.execute("""
            INSERT INTO analysis_patterns (
                pattern_id, pattern_name, domain, question_type, description,
                sql_template, presentation_format, business_context,
                example_input, example_output, tags, created_by,
                created_date, version, status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, [
            new_pattern_id, new_data['pattern_name'], new_data['domain'],
            new_data['question_type'], new_data['description'],
            new_data['sql_template'], new_data['presentation_format'],
            new_data['business_context'], new_data['example_input'],
            new_data['example_output'], tags_json, new_data['created_by'],
            datetime.now().isoformat(), new_version, 'active'
        ])

        # Deprecate old version
        cursor.execute("""
            UPDATE analysis_patterns
            SET status = 'deprecated'
            WHERE pattern_id = ?
        """, [pattern_id])

        # Log version history
        cursor.execute("""
            INSERT INTO pattern_versions (pattern_id, version, changes, previous_version_id)
            VALUES (?, ?, ?, ?)
        """, [new_pattern_id, new_version, changes, pattern_id])

        conn.commit()
        conn.close()

        # Update ChromaDB embedding
        if self.chroma_collection and new_data.get('description'):
            try:
                embed_text = f"{new_data['description']} {new_data.get('example_input', '')}"
                if new_data.get('tags'):
                    embed_text += " " + " ".join(new_data['tags'])

                self.chroma_collection.add(
                    documents=[embed_text],
                    ids=[new_pattern_id],
                    metadatas=[{"domain": new_data['domain'], "pattern_name": new_data['pattern_name']}]
                )
            except Exception as e:
                logger.warning(f"ChromaDB embedding update failed: {e}")

        logger.info(f"Pattern updated: {pattern_id} → {new_pattern_id} (v{new_version})")
        return new_pattern_id

    def delete_pattern(self, pattern_id: str, hard: bool = False) -> bool:
        """
        Delete pattern (soft delete by default).

        Args:
            pattern_id: Pattern to delete
            hard: If True, permanently remove from database

        Returns:
            True if deleted, False if pattern not found
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Check if pattern exists
        cursor.execute("SELECT pattern_id FROM analysis_patterns WHERE pattern_id = ?", [pattern_id])
        if not cursor.fetchone():
            conn.close()
            return False

        if hard:
            # Hard delete - remove from database
            cursor.execute("DELETE FROM analysis_patterns WHERE pattern_id = ?", [pattern_id])

            # Remove from ChromaDB
            if self.chroma_collection:
                try:
                    self.chroma_collection.delete(ids=[pattern_id])
                except Exception as e:
                    logger.warning(f"ChromaDB delete failed: {e}")
        else:
            # Soft delete - mark as archived
            cursor.execute("""
                UPDATE analysis_patterns
                SET status = 'archived'
                WHERE pattern_id = ?
            """, [pattern_id])

        conn.commit()
        conn.close()

        logger.info(f"Pattern {'deleted' if hard else 'archived'}: {pattern_id}")
        return True

    def suggest_pattern(self,
                       user_question: str,
                       domain: str = None,
                       confidence_threshold: float = 0.70) -> Dict[str, Any]:
        """
        Auto-suggest pattern for user's question.

        Args:
            user_question: User's analytical question
            domain: Optional domain hint
            confidence_threshold: Minimum confidence (default: 0.70)

        Returns:
            {
                'matched': bool,
                'confidence': float,
                'pattern': dict or None,
                'pattern_id': str or None
            }
        """
        # Search for matching patterns
        results = self.search_patterns(user_question, domain=domain, limit=1, similarity_threshold=0.0)

        if not results:
            return {
                'matched': False,
                'confidence': 0.0,
                'pattern': None,
                'pattern_id': None
            }

        # Get best match
        pattern, similarity = results[0]

        matched = similarity >= confidence_threshold

        return {
            'matched': matched,
            'confidence': similarity,
            'pattern': pattern if matched else None,
            'pattern_id': pattern['pattern_id'] if matched else None
        }

    def track_usage(self,
                   pattern_id: str,
                   user_question: str,
                   success: bool = True,
                   feedback: str = None):
        """Log pattern usage for analytics."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("""
                INSERT INTO pattern_usage (pattern_id, user_question, success, feedback, used_date)
                VALUES (?, ?, ?, ?, ?)
            """, [pattern_id, user_question, success, feedback, datetime.now().isoformat()])

            conn.commit()
            conn.close()
        except Exception as e:
            logger.warning(f"Usage tracking failed: {e}")
            # Non-blocking - don't fail if tracking fails
