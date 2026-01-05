#!/usr/bin/env python3
"""
Conversation Archive System
Phase 237: Pre-Compaction Learning Capture

Responsibilities:
- Archive full conversations to SQLite before compaction
- Provide retrieval interface for archived conversations
- Track compaction metrics and performance

Author: Maia (Phase 237)
Created: 2026-01-06
"""

import json
import sqlite3
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
from contextlib import contextmanager


class ConversationArchive:
    """
    Manages archival and retrieval of conversation snapshots.

    Thread-safe SQLite operations with retry logic for DB locks.
    """

    def __init__(self, db_path: Optional[Path] = None):
        """
        Initialize archive system.

        Args:
            db_path: Path to archive database (default: ~/.maia/data/conversation_archive.db)
        """
        if db_path is None:
            db_path = Path.home() / ".maia" / "data" / "conversation_archive.db"

        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        # Initialize schema
        self._init_schema()

    def _init_schema(self):
        """Create database schema if it doesn't exist."""
        schema_path = Path(__file__).parent / "archive_schema.sql"

        with open(schema_path) as f:
            schema_sql = f.read()

        with self._get_connection() as conn:
            conn.executescript(schema_sql)
            conn.commit()

    @contextmanager
    def _get_connection(self, timeout: int = 5):
        """
        Get database connection with retry logic.

        Args:
            timeout: Timeout in seconds for DB lock

        Yields:
            sqlite3.Connection
        """
        conn = sqlite3.connect(
            self.db_path,
            timeout=timeout,
            isolation_level=None  # Autocommit mode
        )
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()

    def archive_conversation(
        self,
        context_id: str,
        full_conversation: str,
        trigger_type: str = 'auto',
        session_id: Optional[str] = None,
        transcript_path: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> int:
        """
        Archive a conversation snapshot.

        Args:
            context_id: Claude context window ID
            full_conversation: Complete JSONL conversation
            trigger_type: 'auto' or 'manual'
            session_id: PAI v2 session ID (optional)
            transcript_path: Path to original transcript file
            metadata: Additional metadata (tool usage, learnings, etc.)

        Returns:
            snapshot_id: ID of created snapshot

        Raises:
            sqlite3.IntegrityError: If snapshot already exists for context + timestamp
        """
        metadata = metadata or {}

        # Parse conversation to extract metadata
        messages = self._parse_conversation(full_conversation)
        message_count = len(messages)

        # Extract first and last messages
        first_message = messages[0].get('content', '')[:500] if messages else ''
        last_message = messages[-1].get('content', '')[:500] if messages else ''

        # Estimate tokens (rough approximation: 1 token ≈ 4 chars)
        token_estimate = len(full_conversation) // 4

        # Prepare data
        snapshot_data = {
            'context_id': context_id,
            'session_id': session_id,
            'snapshot_timestamp': int(time.time() * 1000),  # Millisecond precision
            'trigger_type': trigger_type,
            'transcript_path': transcript_path,
            'full_conversation': full_conversation,
            'message_count': message_count,
            'token_estimate': token_estimate,
            'learning_count': metadata.get('learning_count', 0),
            'learning_ids': json.dumps(metadata.get('learning_ids', [])),
            'tool_usage_stats': json.dumps(metadata.get('tool_usage', {})),
            'agents_used': json.dumps(metadata.get('agents_used', [])),
            'error_count': metadata.get('error_count', 0),
            'first_message': first_message,
            'last_message': last_message,
            'topics': json.dumps(metadata.get('topics', []))
        }

        # Insert into database
        with self._get_connection() as conn:
            cursor = conn.execute("""
                INSERT INTO conversation_snapshots (
                    context_id, session_id, snapshot_timestamp, trigger_type,
                    transcript_path, full_conversation, message_count, token_estimate,
                    learning_count, learning_ids, tool_usage_stats, agents_used,
                    error_count, first_message, last_message, topics
                )
                VALUES (
                    :context_id, :session_id, :snapshot_timestamp, :trigger_type,
                    :transcript_path, :full_conversation, :message_count, :token_estimate,
                    :learning_count, :learning_ids, :tool_usage_stats, :agents_used,
                    :error_count, :first_message, :last_message, :topics
                )
            """, snapshot_data)

            snapshot_id = cursor.lastrowid

        return snapshot_id

    def get_conversation(
        self,
        context_id: str,
        before_timestamp: Optional[int] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Retrieve archived conversation for a context.

        Args:
            context_id: Claude context window ID
            before_timestamp: Get snapshot before this time (default: latest)

        Returns:
            Snapshot data with parsed messages, or None if not found
        """
        with self._get_connection() as conn:
            if before_timestamp:
                cursor = conn.execute("""
                    SELECT * FROM conversation_snapshots
                    WHERE context_id = ?
                      AND snapshot_timestamp < ?
                    ORDER BY snapshot_timestamp DESC
                    LIMIT 1
                """, (context_id, before_timestamp))
            else:
                cursor = conn.execute("""
                    SELECT * FROM conversation_snapshots
                    WHERE context_id = ?
                    ORDER BY snapshot_timestamp DESC
                    LIMIT 1
                """, (context_id,))

            row = cursor.fetchone()

        if not row:
            return None

        return self._row_to_dict(row)

    def search_conversations(
        self,
        query: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Search archived conversations using full-text search.

        Args:
            query: Search keywords
            limit: Maximum results to return

        Returns:
            List of matching snapshots with relevance scores
        """
        with self._get_connection() as conn:
            cursor = conn.execute("""
                SELECT
                    cs.*,
                    rank AS relevance_score
                FROM conversation_search
                JOIN conversation_snapshots cs ON cs.snapshot_id = conversation_search.rowid
                WHERE conversation_search MATCH ?
                ORDER BY rank
                LIMIT ?
            """, (query, limit))

            rows = cursor.fetchall()

        return [self._row_to_dict(row) for row in rows]

    def get_compaction_history(
        self,
        context_id: str
    ) -> List[Dict[str, Any]]:
        """
        Get timeline of compaction events for a context.

        Args:
            context_id: Claude context window ID

        Returns:
            List of compaction events ordered by timestamp
        """
        with self._get_connection() as conn:
            cursor = conn.execute("""
                SELECT
                    snapshot_id,
                    snapshot_timestamp,
                    trigger_type,
                    message_count,
                    learning_count,
                    token_estimate
                FROM conversation_snapshots
                WHERE context_id = ?
                ORDER BY snapshot_timestamp ASC
            """, (context_id,))

            rows = cursor.fetchall()

        return [dict(row) for row in rows]

    def log_compaction_metric(
        self,
        context_id: str,
        trigger_type: str,
        execution_time_ms: int,
        messages_processed: int,
        learnings_extracted: int,
        success: bool,
        snapshot_id: Optional[int] = None,
        error_message: Optional[str] = None
    ):
        """
        Log compaction performance metrics.

        Args:
            context_id: Claude context window ID
            trigger_type: 'auto' or 'manual'
            execution_time_ms: Hook execution time in milliseconds
            messages_processed: Number of messages in conversation
            learnings_extracted: Number of learnings captured
            success: Whether compaction succeeded
            snapshot_id: Reference to created snapshot (if successful)
            error_message: Error details (if failed)
        """
        with self._get_connection() as conn:
            conn.execute("""
                INSERT INTO compaction_metrics (
                    context_id, compaction_timestamp, trigger_type,
                    execution_time_ms, messages_processed, learnings_extracted,
                    success, error_message, snapshot_id
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                context_id,
                int(time.time() * 1000),  # Millisecond precision
                trigger_type,
                execution_time_ms,
                messages_processed,
                learnings_extracted,
                success,
                error_message,
                snapshot_id
            ))

    def _parse_conversation(self, full_conversation: str) -> List[Dict[str, Any]]:
        """
        Parse JSONL conversation into message list.

        Args:
            full_conversation: JSONL formatted conversation

        Returns:
            List of message dictionaries
        """
        messages = []
        for line in full_conversation.strip().split('\n'):
            if line.strip():
                try:
                    messages.append(json.loads(line))
                except json.JSONDecodeError:
                    # Skip malformed lines
                    continue
        return messages

    def _row_to_dict(self, row: sqlite3.Row) -> Dict[str, Any]:
        """
        Convert SQLite row to dictionary with parsed JSON fields.

        Args:
            row: SQLite row object

        Returns:
            Dictionary with parsed data
        """
        data = dict(row)

        # Parse JSON fields
        for field in ['learning_ids', 'tool_usage_stats', 'agents_used', 'topics']:
            if field in data and data[field]:
                try:
                    data[field] = json.loads(data[field])
                except json.JSONDecodeError:
                    data[field] = []

        # Parse conversation messages
        if 'full_conversation' in data:
            data['messages'] = self._parse_conversation(data['full_conversation'])

        return data


def get_archive(db_path: Optional[Path] = None) -> ConversationArchive:
    """
    Get conversation archive instance (singleton pattern).

    Args:
        db_path: Optional override for database path

    Returns:
        ConversationArchive instance
    """
    if not hasattr(get_archive, '_instance'):
        get_archive._instance = ConversationArchive(db_path)
    return get_archive._instance
