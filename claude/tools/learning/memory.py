#!/usr/bin/env python3
"""
Maia Memory System

Auto-generates session summaries for cross-session learning:
- Summarizes key decisions and outcomes
- Enables full-text search across sessions
- Privacy-first (all data stays in ~/.maia/)
"""

import hashlib
import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class MemorySummary:
    """A Maia Memory session summary."""
    id: str
    session_id: str
    started_at: str
    ended_at: Optional[str]
    initial_query: str
    agent_used: Optional[str]
    domain: Optional[str]
    summary_text: str
    key_decisions: List[str]
    tools_used: Dict[str, int]
    verify_success: bool
    verify_confidence: float


class MaiaMemory:
    """Manages Maia Memory session summaries."""

    def __init__(self):
        self.db_path = Path.home() / ".maia" / "memory" / "memory.db"
        self.summaries_dir = Path.home() / ".maia" / "memory" / "summaries"
        self._ensure_initialized()

    def _ensure_initialized(self):
        """Ensure database exists."""
        if not self.db_path.exists():
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
            from claude.tools.learning.schema import init_memory_db
            conn = init_memory_db(self.db_path)
            conn.close()
        self.summaries_dir.mkdir(parents=True, exist_ok=True)

    def _get_conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _ensure_prompts_initialized(self):
        """Ensure prompts table exists in database."""
        from claude.tools.learning.schema import PROMPTS_SCHEMA
        conn = self._get_conn()
        conn.executescript(PROMPTS_SCHEMA)
        conn.commit()
        conn.close()

    # =========================================================================
    # Prompt Capture Methods (SPRINT-002-PROMPT-CAPTURE)
    # =========================================================================

    def capture_prompt(
        self,
        session_id: str,
        context_id: str,
        prompt_text: str,
        agent_active: Optional[str] = None
    ) -> int:
        """
        Capture a user prompt.

        Args:
            session_id: PAI v2 session ID
            context_id: Claude context window ID
            prompt_text: The user's prompt text
            agent_active: Currently active agent (optional)

        Returns:
            prompt_id: ID of the captured prompt
        """
        self._ensure_prompts_initialized()

        conn = self._get_conn()

        # Get next prompt index for this session
        cursor = conn.execute(
            "SELECT COALESCE(MAX(prompt_index), -1) + 1 FROM session_prompts WHERE session_id = ?",
            (session_id,)
        )
        prompt_index = cursor.fetchone()[0]

        # Calculate metrics
        char_count = len(prompt_text)
        word_count = len(prompt_text.split())
        prompt_hash = hashlib.sha256(prompt_text.encode()).hexdigest()

        # Insert prompt
        cursor = conn.execute("""
            INSERT INTO session_prompts
            (session_id, context_id, prompt_index, prompt_text, timestamp, char_count, word_count, agent_active, prompt_hash)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            session_id,
            context_id,
            prompt_index,
            prompt_text,
            datetime.now().isoformat(),
            char_count,
            word_count,
            agent_active,
            prompt_hash
        ))

        prompt_id = cursor.lastrowid
        conn.commit()
        conn.close()

        return prompt_id

    def get_prompts_for_session(self, session_id: str) -> List[Dict[str, Any]]:
        """
        Get all prompts for a session.

        Args:
            session_id: PAI v2 session ID

        Returns:
            List of prompt records ordered by prompt_index
        """
        self._ensure_prompts_initialized()

        conn = self._get_conn()
        cursor = conn.execute("""
            SELECT * FROM session_prompts
            WHERE session_id = ?
            ORDER BY prompt_index ASC
        """, (session_id,))

        results = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return results

    def search_prompts(self, query: str, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Full-text search across prompts.

        Args:
            query: Search query (FTS5 syntax supported)
            limit: Maximum results

        Returns:
            List of matching prompts with relevance scores
        """
        self._ensure_prompts_initialized()

        conn = self._get_conn()
        cursor = conn.execute("""
            SELECT p.*, rank
            FROM session_prompts p
            JOIN prompts_fts f ON p.prompt_id = f.rowid
            WHERE prompts_fts MATCH ?
            ORDER BY rank
            LIMIT ?
        """, (query, limit))

        results = []
        for row in cursor.fetchall():
            result = dict(row)
            result['relevance'] = -result.pop('rank')  # FTS5 rank is negative
            results.append(result)

        conn.close()
        return results

    def get_prompt_stats(self, session_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Get prompt statistics.

        Args:
            session_id: Optional session filter

        Returns:
            Statistics dictionary
        """
        self._ensure_prompts_initialized()

        conn = self._get_conn()

        if session_id:
            cursor = conn.execute("""
                SELECT
                    COUNT(*) as prompt_count,
                    COALESCE(SUM(char_count), 0) as total_chars,
                    COALESCE(SUM(word_count), 0) as total_words,
                    COALESCE(AVG(char_count), 0) as avg_chars_per_prompt
                FROM session_prompts
                WHERE session_id = ?
            """, (session_id,))
        else:
            cursor = conn.execute("""
                SELECT
                    COUNT(*) as prompt_count,
                    COUNT(DISTINCT session_id) as unique_sessions,
                    COALESCE(SUM(char_count), 0) as total_chars,
                    COALESCE(SUM(word_count), 0) as total_words,
                    COALESCE(AVG(char_count), 0) as avg_chars_per_prompt
                FROM session_prompts
            """)

        row = cursor.fetchone()
        conn.close()

        return dict(row)

    def start_session(
        self,
        session_id: str,
        context_id: str,
        initial_query: str,
        agent_used: Optional[str] = None,
        domain: Optional[str] = None
    ) -> str:
        """Record session start."""
        conn = self._get_conn()
        conn.execute("""
            INSERT INTO sessions (id, context_id, started_at, initial_query, agent_used, domain, status)
            VALUES (?, ?, ?, ?, ?, ?, 'active')
        """, (session_id, context_id, datetime.now().isoformat(), initial_query, agent_used, domain))
        conn.commit()
        conn.close()
        return session_id

    def end_session(
        self,
        session_id: str,
        summary_text: str,
        key_decisions: List[str],
        tools_used: Dict[str, int],
        files_touched: List[str],
        verify_success: bool,
        verify_confidence: float,
        verify_metrics: Dict[str, Any],
        learn_insights: List[Dict[str, Any]],
        status: str = 'completed'
    ):
        """Record session end with summary."""
        conn = self._get_conn()
        conn.execute("""
            UPDATE sessions SET
                ended_at = ?,
                status = ?,
                summary_text = ?,
                key_decisions = ?,
                tools_used = ?,
                files_touched = ?,
                verify_success = ?,
                verify_confidence = ?,
                verify_metrics = ?,
                learn_insights = ?,
                patterns_extracted = ?
            WHERE id = ?
        """, (
            datetime.now().isoformat(),
            status,
            summary_text,
            json.dumps(key_decisions),
            json.dumps(tools_used),
            json.dumps(files_touched),
            verify_success,
            verify_confidence,
            json.dumps(verify_metrics),
            json.dumps(learn_insights),
            len(learn_insights),
            session_id
        ))
        conn.commit()
        conn.close()

        # Write summary file
        self._write_summary_file(session_id, summary_text, key_decisions, tools_used)

    def _write_summary_file(
        self,
        session_id: str,
        summary_text: str,
        key_decisions: List[str],
        tools_used: Dict[str, int]
    ):
        """Write human-readable summary file."""
        date_dir = self.summaries_dir / datetime.now().strftime("%Y-%m-%d")
        date_dir.mkdir(exist_ok=True)

        content = f"""# Session: {session_id}

## Summary
{summary_text}

## Key Decisions
{chr(10).join(f'- {d}' for d in key_decisions) if key_decisions else '- None recorded'}

## Tools Used
{chr(10).join(f'- {tool}: {count}x' for tool, count in tools_used.items()) if tools_used else '- None'}
"""
        (date_dir / f"{session_id}.md").write_text(content)

    def search(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Full-text search across sessions."""
        conn = self._get_conn()
        cursor = conn.execute("""
            SELECT s.*, rank
            FROM sessions s
            JOIN sessions_fts f ON s.id = f.id
            WHERE sessions_fts MATCH ?
            ORDER BY rank
            LIMIT ?
        """, (query, limit))

        results = []
        for row in cursor.fetchall():
            results.append({
                'id': row['id'],
                'started_at': row['started_at'],
                'initial_query': row['initial_query'],
                'summary_text': row['summary_text'],
                'agent_used': row['agent_used'],
                'domain': row['domain'],
                'verify_success': row['verify_success'],
                'relevance': -row['rank']  # FTS5 rank is negative
            })

        conn.close()
        return results

    def get_recent(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent sessions."""
        conn = self._get_conn()
        cursor = conn.execute("""
            SELECT * FROM sessions
            ORDER BY started_at DESC
            LIMIT ?
        """, (limit,))

        results = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return results

    def get_by_domain(self, domain: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get sessions by domain."""
        conn = self._get_conn()
        cursor = conn.execute("""
            SELECT * FROM sessions
            WHERE domain = ?
            ORDER BY started_at DESC
            LIMIT ?
        """, (domain, limit))

        results = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return results

    def get_context_for_query(self, query: str, limit: int = 3) -> str:
        """Get relevant context to inject for a new query."""
        results = self.search(query, limit)

        if not results:
            return ""

        context_parts = ["## Relevant Prior Sessions\n"]
        for r in results:
            context_parts.append(f"""
### {r['started_at'][:10]} - {r['initial_query'][:100]}
{r['summary_text'][:500] if r['summary_text'] else 'No summary available'}
""")

        return "\n".join(context_parts)


# Singleton
_memory: Optional[MaiaMemory] = None


def get_memory() -> MaiaMemory:
    """Get Maia Memory singleton."""
    global _memory
    if _memory is None:
        _memory = MaiaMemory()
    return _memory


__all__ = ["MaiaMemory", "MemorySummary", "get_memory"]
