#!/usr/bin/env python3
"""
PAI v2 Bridge for Pre-Compaction Learning Capture

Connects the pre-compaction hook with PAI v2's pattern storage.
Extracted learnings from conversations are saved as patterns in the learning database.

Phase 237 Phase 2: Learning ID tracking
"""

import uuid
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional


# Map extraction learning types to PAI v2 pattern types
LEARNING_TYPE_MAPPING = {
    'decision': 'workflow',        # Decision patterns → workflow patterns
    'solution': 'tool_sequence',   # Solution approaches → tool sequences
    'outcome': 'workflow',         # Outcomes → workflow patterns
    'handoff': 'workflow',         # Agent handoffs → workflow patterns
    'checkpoint': 'workflow',      # Checkpoints → workflow patterns
}


class PAIv2Bridge:
    """
    Bridge between pre-compaction extraction and PAI v2 pattern storage.

    Converts extracted learnings into PAI v2 patterns and stores them
    in the learning database with proper IDs for tracking.
    """

    def __init__(self):
        """Initialize bridge with connection to learning database."""
        self.db_path = Path.home() / ".maia" / "learning" / "learning.db"
        self._ensure_initialized()

    def _ensure_initialized(self):
        """Ensure learning database exists."""
        if not self.db_path.exists():
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
            from claude.tools.learning.schema import init_learning_db
            conn = init_learning_db(self.db_path)
            conn.close()

    def _get_conn(self) -> sqlite3.Connection:
        """Get database connection."""
        conn = sqlite3.Connection(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def save_learnings_as_patterns(
        self,
        learnings: List[Dict[str, Any]],
        context_id: str,
        session_id: Optional[str] = None,
        domain: Optional[str] = None
    ) -> List[str]:
        """
        Save extracted learnings as PAI v2 patterns.

        Args:
            learnings: List of learning dictionaries from extraction engine
                Format: [{'type': str, 'content': str, 'timestamp': str, 'context': dict}, ...]
            context_id: Claude context window ID
            session_id: PAI v2 session ID (if available)
            domain: Domain/category (optional)

        Returns:
            List of pattern IDs created in learning database

        Example:
            >>> bridge = PAIv2Bridge()
            >>> learnings = [
            ...     {'type': 'decision', 'content': 'chose SQLite for simplicity', ...},
            ...     {'type': 'solution', 'content': 'fixed by adding retry logic', ...}
            ... ]
            >>> pattern_ids = bridge.save_learnings_as_patterns(learnings, 'ctx_123')
            >>> len(pattern_ids)
            2
        """
        if not learnings:
            return []

        pattern_ids = []
        conn = self._get_conn()

        try:
            for learning in learnings:
                pattern_id = self._create_pattern(
                    conn=conn,
                    learning=learning,
                    context_id=context_id,
                    session_id=session_id,
                    domain=domain
                )
                pattern_ids.append(pattern_id)

            conn.commit()
            return pattern_ids

        except Exception as e:
            conn.rollback()
            raise RuntimeError(f"Failed to save learnings as patterns: {e}") from e

        finally:
            conn.close()

    def _create_pattern(
        self,
        conn: sqlite3.Connection,
        learning: Dict[str, Any],
        context_id: str,
        session_id: Optional[str],
        domain: Optional[str]
    ) -> str:
        """
        Create a single pattern from a learning.

        Args:
            conn: Database connection
            learning: Learning dictionary
            context_id: Context ID
            session_id: Session ID
            domain: Domain

        Returns:
            Pattern ID
        """
        import json

        pattern_id = f"pat_{uuid.uuid4().hex[:12]}"
        learning_type = learning.get('type', 'unknown')
        pattern_type = LEARNING_TYPE_MAPPING.get(learning_type, 'workflow')

        description = learning.get('content', '')
        timestamp = learning.get('timestamp', datetime.now().isoformat())

        # Build pattern_data with context
        pattern_data = {
            'original_type': learning_type,
            'context_id': context_id,
            'session_id': session_id,
            'extracted_at': timestamp,
            'context': learning.get('context', {})
        }

        # Default confidence based on learning type
        confidence_map = {
            'decision': 0.8,    # High confidence in explicit decisions
            'solution': 0.9,    # Very high confidence in solutions
            'outcome': 0.7,     # Medium confidence in outcomes
            'handoff': 0.6,     # Medium confidence in handoffs
            'checkpoint': 0.5,  # Lower confidence in checkpoints
        }
        confidence = confidence_map.get(learning_type, 0.5)

        # Insert pattern
        conn.execute("""
            INSERT INTO patterns (
                id, pattern_type, domain, description, pattern_data,
                confidence, occurrence_count, first_seen, last_seen, decayed_confidence
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            pattern_id,
            pattern_type,
            domain,
            description,
            json.dumps(pattern_data),
            confidence,
            1,  # First occurrence
            timestamp,
            timestamp,
            confidence  # No decay yet
        ))

        return pattern_id

    def get_pattern(self, pattern_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a pattern by ID.

        Args:
            pattern_id: Pattern ID

        Returns:
            Pattern dictionary or None if not found
        """
        import json

        conn = self._get_conn()
        try:
            row = conn.execute(
                "SELECT * FROM patterns WHERE id = ?",
                (pattern_id,)
            ).fetchone()

            if not row:
                return None

            return {
                'id': row['id'],
                'pattern_type': row['pattern_type'],
                'domain': row['domain'],
                'description': row['description'],
                'pattern_data': json.loads(row['pattern_data']) if row['pattern_data'] else {},
                'confidence': row['confidence'],
                'occurrence_count': row['occurrence_count'],
                'first_seen': row['first_seen'],
                'last_seen': row['last_seen'],
                'decayed_confidence': row['decayed_confidence']
            }
        finally:
            conn.close()

    def get_patterns_for_context(self, context_id: str) -> List[Dict[str, Any]]:
        """
        Get all patterns extracted from a specific context.

        Args:
            context_id: Context ID

        Returns:
            List of pattern dictionaries
        """
        import json

        conn = self._get_conn()
        try:
            rows = conn.execute("""
                SELECT * FROM patterns
                WHERE json_extract(pattern_data, '$.context_id') = ?
                ORDER BY last_seen DESC
            """, (context_id,)).fetchall()

            patterns = []
            for row in rows:
                patterns.append({
                    'id': row['id'],
                    'pattern_type': row['pattern_type'],
                    'domain': row['domain'],
                    'description': row['description'],
                    'pattern_data': json.loads(row['pattern_data']) if row['pattern_data'] else {},
                    'confidence': row['confidence'],
                    'occurrence_count': row['occurrence_count'],
                    'first_seen': row['first_seen'],
                    'last_seen': row['last_seen']
                })

            return patterns
        finally:
            conn.close()


# Singleton instance
_bridge: Optional[PAIv2Bridge] = None


def get_pai_v2_bridge() -> PAIv2Bridge:
    """Get PAI v2 bridge singleton instance."""
    global _bridge
    if _bridge is None:
        _bridge = PAIv2Bridge()
    return _bridge


__all__ = ['PAIv2Bridge', 'get_pai_v2_bridge', 'LEARNING_TYPE_MAPPING']
