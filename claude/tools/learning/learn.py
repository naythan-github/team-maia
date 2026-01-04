#!/usr/bin/env python3
"""
LEARN Phase - Pattern Extraction

Extracts learnings from session for personal improvement:
- Pattern recognition (successful tool sequences)
- Preference inference (from corrections)
- Workflow detection (repeated approaches)
"""

import json
import sqlite3
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict


@dataclass
class LearningInsight:
    """A learning insight extracted from session."""
    insight_type: str  # 'workflow', 'tool_sequence', 'preference', 'correction'
    domain: Optional[str]
    description: str
    confidence: float
    data: Dict[str, Any]


class LearnPhase:
    """Implements LEARN phase logic."""

    MIN_CONFIDENCE = 0.5
    PATTERN_THRESHOLD = 3  # Minimum occurrences for pattern

    def __init__(self):
        self.db_path = Path.home() / ".maia" / "learning" / "learning.db"
        self._ensure_initialized()

    def _ensure_initialized(self):
        if not self.db_path.exists():
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
            from claude.tools.learning.schema import init_learning_db
            conn = init_learning_db(self.db_path)
            conn.close()

    def _get_conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def learn(
        self,
        session_id: str,
        uocs_summary: Dict[str, Any],
        session_data: Dict[str, Any],
        verify_success: bool
    ) -> List[LearningInsight]:
        """
        Extract learning insights from session.

        Args:
            session_id: Session identifier
            uocs_summary: From UOCS.get_summary()
            session_data: Session metadata
            verify_success: From VERIFY phase

        Returns:
            List of extracted insights
        """
        insights = []

        # Only learn from successful sessions
        if not verify_success:
            return insights

        # Extract tool sequence pattern
        tool_sequence = self._extract_tool_sequence(uocs_summary)
        if tool_sequence:
            insights.append(tool_sequence)

        # Extract domain pattern
        domain_pattern = self._extract_domain_pattern(session_data, uocs_summary)
        if domain_pattern:
            insights.append(domain_pattern)

        # Store insights
        for insight in insights:
            self._store_pattern(session_id, insight)

        return insights

    def _extract_tool_sequence(self, uocs_summary: Dict[str, Any]) -> Optional[LearningInsight]:
        """Extract successful tool sequence pattern."""
        tools_used = uocs_summary.get('tools_used', {})

        if len(tools_used) < 2:
            return None

        # Top 5 tools by usage
        top_tools = sorted(tools_used.items(), key=lambda x: x[1], reverse=True)[:5]
        sequence = [t[0] for t in top_tools]

        return LearningInsight(
            insight_type='tool_sequence',
            domain=None,
            description=f"Successful pattern: {' -> '.join(sequence)}",
            confidence=uocs_summary.get('success_rate', 0.5),
            data={'sequence': sequence, 'counts': dict(top_tools)}
        )

    def _extract_domain_pattern(
        self,
        session_data: Dict[str, Any],
        uocs_summary: Dict[str, Any]
    ) -> Optional[LearningInsight]:
        """Extract domain-specific pattern."""
        domain = session_data.get('domain')
        agent = session_data.get('agent_used')

        if not domain and not agent:
            return None

        return LearningInsight(
            insight_type='workflow',
            domain=domain,
            description=f"Domain workflow: {domain or 'general'} with {agent or 'no agent'}",
            confidence=0.6,
            data={
                'domain': domain,
                'agent': agent,
                'tools': list(uocs_summary.get('tools_used', {}).keys())
            }
        )

    def _store_pattern(self, session_id: str, insight: LearningInsight):
        """Store pattern in database, updating confidence if exists."""
        conn = self._get_conn()

        # Check if similar pattern exists
        cursor = conn.execute("""
            SELECT id, occurrence_count, confidence
            FROM patterns
            WHERE pattern_type = ? AND domain IS ?
            LIMIT 1
        """, (insight.insight_type, insight.domain))

        existing = cursor.fetchone()

        if existing:
            # Update existing pattern
            new_count = existing['occurrence_count'] + 1
            # Increase confidence with more occurrences (max 0.95)
            new_confidence = min(0.95, existing['confidence'] + 0.05)

            conn.execute("""
                UPDATE patterns SET
                    occurrence_count = ?,
                    confidence = ?,
                    last_seen = ?,
                    pattern_data = ?
                WHERE id = ?
            """, (new_count, new_confidence, datetime.now().isoformat(),
                  json.dumps(insight.data), existing['id']))
        else:
            # Insert new pattern
            conn.execute("""
                INSERT INTO patterns (id, pattern_type, domain, description, pattern_data,
                                      confidence, first_seen, last_seen)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (str(uuid.uuid4())[:8], insight.insight_type, insight.domain,
                  insight.description, json.dumps(insight.data), insight.confidence,
                  datetime.now().isoformat(), datetime.now().isoformat()))

        conn.commit()
        conn.close()

    def get_patterns(self, domain: Optional[str] = None, min_confidence: float = 0.5) -> List[Dict]:
        """Get stored patterns."""
        conn = self._get_conn()

        if domain:
            cursor = conn.execute("""
                SELECT * FROM patterns
                WHERE domain = ? AND confidence >= ?
                ORDER BY confidence DESC
            """, (domain, min_confidence))
        else:
            cursor = conn.execute("""
                SELECT * FROM patterns
                WHERE confidence >= ?
                ORDER BY confidence DESC
            """, (min_confidence,))

        results = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return results

    def record_preference(
        self,
        category: str,
        key: str,
        value: str,
        session_id: str,
        confidence: float = 0.6
    ):
        """Record a user preference (from correction or explicit setting)."""
        conn = self._get_conn()

        # Check if exists
        cursor = conn.execute("""
            SELECT id, source_sessions, confidence
            FROM preferences
            WHERE category = ? AND key = ?
        """, (category, key))

        existing = cursor.fetchone()

        if existing:
            # Update
            sources = json.loads(existing['source_sessions'] or '[]')
            sources.append(session_id)
            new_confidence = min(0.95, existing['confidence'] + 0.1)

            conn.execute("""
                UPDATE preferences SET
                    value = ?,
                    confidence = ?,
                    source_sessions = ?,
                    updated_at = ?
                WHERE category = ? AND key = ?
            """, (value, new_confidence, json.dumps(sources[-10:]),  # Keep last 10
                  datetime.now().isoformat(), category, key))
        else:
            # Insert
            conn.execute("""
                INSERT INTO preferences (id, category, key, value, confidence, source_sessions, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (str(uuid.uuid4())[:8], category, key, value, confidence,
                  json.dumps([session_id]), datetime.now().isoformat(), datetime.now().isoformat()))

        conn.commit()
        conn.close()

    def get_preferences(self, category: Optional[str] = None) -> Dict[str, Any]:
        """Get stored preferences."""
        conn = self._get_conn()

        if category:
            cursor = conn.execute("""
                SELECT category, key, value, confidence
                FROM preferences
                WHERE category = ?
                ORDER BY confidence DESC
            """, (category,))
        else:
            cursor = conn.execute("""
                SELECT category, key, value, confidence
                FROM preferences
                ORDER BY category, confidence DESC
            """)

        prefs = {}
        for row in cursor.fetchall():
            cat = row['category']
            if cat not in prefs:
                prefs[cat] = {}
            prefs[cat][row['key']] = {
                'value': row['value'],
                'confidence': row['confidence']
            }

        conn.close()
        return prefs

    def to_dict(self, insights: List[LearningInsight]) -> List[Dict]:
        """Convert insights to dict for storage."""
        return [asdict(i) for i in insights]


# Singleton
_learn: Optional[LearnPhase] = None


def get_learn() -> LearnPhase:
    """Get LearnPhase singleton."""
    global _learn
    if _learn is None:
        _learn = LearnPhase()
    return _learn


__all__ = ["LearnPhase", "LearningInsight", "get_learn"]
