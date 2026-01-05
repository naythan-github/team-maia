#!/usr/bin/env python3
"""
Self-modification Module

Phase 234: Update preferences and suggest prompt updates based on learnings.
"""

import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional

# Configuration
MAX_UPDATES_PER_SESSION = 20
MIN_CONFIDENCE_FOR_SUGGESTION = 0.75
PROTECTED_FILES = {'identity.md', 'ufc_system.md', 'systematic_thinking.md'}

# Paths
MAIA_ROOT = Path(__file__).parent.parent.parent.parent
USER_PREFERENCES_PATH = MAIA_ROOT / "claude" / "data" / "user_preferences.json"


def _get_db_path() -> Path:
    """Get path to learned preferences database."""
    db_dir = Path.home() / ".maia" / "learning"
    db_dir.mkdir(parents=True, exist_ok=True)
    return db_dir / "preferences.db"


def _init_db() -> sqlite3.Connection:
    """Initialize preferences database."""
    db_path = _get_db_path()
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row

    conn.executescript("""
        CREATE TABLE IF NOT EXISTS preferences (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category TEXT NOT NULL,
            key TEXT NOT NULL,
            value TEXT NOT NULL,
            confidence REAL NOT NULL,
            occurrence_count INTEGER DEFAULT 1,
            source_sessions TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            UNIQUE(category, key)
        );

        CREATE TABLE IF NOT EXISTS modification_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            action TEXT NOT NULL,
            category TEXT,
            key TEXT,
            old_value TEXT,
            new_value TEXT,
            confidence REAL,
            timestamp TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS prompt_suggestions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pattern_type TEXT NOT NULL,
            target_file TEXT NOT NULL,
            suggestion TEXT NOT NULL,
            confidence REAL NOT NULL,
            status TEXT DEFAULT 'pending',
            created_at TEXT NOT NULL
        );
    """)

    conn.commit()
    return conn


def update_preference(
    category: str,
    key: str,
    value: str,
    confidence: float,
    source_session: str
) -> Dict[str, Any]:
    """
    Update or create a learned preference.

    Args:
        category: Preference category (coding_style, tool_choice, etc.)
        key: Preference key
        value: Preference value
        confidence: Confidence score (0-1)
        source_session: Session ID that generated this preference

    Returns:
        Update result dict
    """
    conn = _init_db()
    now = datetime.now().isoformat()

    try:
        # Check if preference exists
        cursor = conn.execute(
            "SELECT * FROM preferences WHERE category = ? AND key = ?",
            (category, key)
        )
        existing = cursor.fetchone()

        if existing:
            # Update existing - increase confidence and occurrence count
            new_confidence = min(existing['confidence'] + (confidence * 0.1), 0.99)
            new_count = existing['occurrence_count'] + 1

            sessions = json.loads(existing['source_sessions'] or '[]')
            if source_session not in sessions:
                sessions.append(source_session)

            conn.execute("""
                UPDATE preferences
                SET value = ?, confidence = ?, occurrence_count = ?,
                    source_sessions = ?, updated_at = ?
                WHERE category = ? AND key = ?
            """, (value, new_confidence, new_count, json.dumps(sessions), now, category, key))

            action = 'updated'
        else:
            # Create new
            conn.execute("""
                INSERT INTO preferences (category, key, value, confidence, source_sessions, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (category, key, value, confidence, json.dumps([source_session]), now, now))

            action = 'created'

        # Log modification
        conn.execute("""
            INSERT INTO modification_log (session_id, action, category, key, new_value, confidence, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (source_session, action, category, key, value, confidence, now))

        conn.commit()

        return {'updated': True, 'action': action}

    except Exception as e:
        conn.rollback()
        return {'updated': False, 'error': str(e)}
    finally:
        conn.close()


def get_preference(category: str, key: str) -> Optional[Dict[str, Any]]:
    """
    Get a stored preference.

    Args:
        category: Preference category
        key: Preference key

    Returns:
        Preference dict or None
    """
    conn = _init_db()

    try:
        cursor = conn.execute(
            "SELECT * FROM preferences WHERE category = ? AND key = ?",
            (category, key)
        )
        row = cursor.fetchone()

        if row:
            return dict(row)
        return None
    finally:
        conn.close()


def list_preferences(category: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    List all stored preferences.

    Args:
        category: Optional category filter

    Returns:
        List of preference dicts
    """
    conn = _init_db()

    try:
        if category:
            cursor = conn.execute(
                "SELECT * FROM preferences WHERE category = ? ORDER BY confidence DESC",
                (category,)
            )
        else:
            cursor = conn.execute(
                "SELECT * FROM preferences ORDER BY category, confidence DESC"
            )

        return [dict(row) for row in cursor.fetchall()]
    finally:
        conn.close()


def sync_to_user_preferences(learned_prefs: Dict[str, Any]) -> Dict[str, Any]:
    """
    Sync learned preferences to user_preferences.json.

    Args:
        learned_prefs: Dict of learned preferences by category

    Returns:
        Sync result dict
    """
    try:
        # Read existing preferences
        if USER_PREFERENCES_PATH.exists():
            existing = json.loads(USER_PREFERENCES_PATH.read_text())
        else:
            existing = {}

        # Add learned preferences section
        existing['learned_preferences'] = learned_prefs
        existing['learned_preferences_updated'] = datetime.now().isoformat()

        # Write back
        USER_PREFERENCES_PATH.write_text(json.dumps(existing, indent=2))

        return {'synced': True}

    except Exception as e:
        return {'synced': False, 'error': str(e)}


def suggest_prompt_update(pattern: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Generate a prompt update suggestion based on a learned pattern.

    Args:
        pattern: Pattern dict with type, description, confidence, etc.

    Returns:
        Suggestion dict or None if no suggestion warranted
    """
    confidence = pattern.get('confidence', 0)
    occurrence_count = pattern.get('occurrence_count', 1)

    # Require high confidence for suggestions
    if confidence < MIN_CONFIDENCE_FOR_SUGGESTION:
        return {'skip_reason': 'low_confidence'}

    # Check for protected files
    target_hint = pattern.get('target_hint', '')
    if target_hint and any(pf in target_hint for pf in PROTECTED_FILES):
        return {'blocked': True, 'reason': 'protected_file'}

    # Determine target file
    domain = pattern.get('domain', 'general')
    pattern_type = pattern.get('type', 'workflow')

    if domain and domain != 'general':
        target_file = f"claude/agents/{domain}_principal_engineer_agent.md"
    else:
        target_file = "claude/context/core/working_principles.md"

    description = pattern.get('description', '')

    # Generate suggestion
    suggestion = {
        'suggestion': f"Add guidance: {description}",
        'target_file': target_file,
        'pattern_type': pattern_type,
        'confidence': confidence,
        'occurrence_count': occurrence_count,
        'requires_approval': True,
        'diff': f"+## Learned Pattern\n+{description}",
    }

    return suggestion


def process_learnings(
    learnings: Dict[str, Any],
    session_id: str
) -> Dict[str, Any]:
    """
    Process learnings from LEARN phase and update system.

    Args:
        learnings: Output from LEARN phase
        session_id: Current session ID

    Returns:
        Processing result with counts and suggestions
    """
    result = {
        'preferences_updated': 0,
        'suggestions': [],
    }

    # Process explicit preferences
    for pref in learnings.get('preferences', []):
        update_result = update_preference(
            category=pref.get('category', 'general'),
            key=pref.get('key', 'preference'),
            value=pref.get('value', ''),
            confidence=pref.get('confidence', 0.5),
            source_session=session_id
        )
        if update_result.get('updated'):
            result['preferences_updated'] += 1

    # Generate prompt suggestions from patterns
    for pattern in learnings.get('patterns', []):
        suggestion = suggest_prompt_update(pattern)
        if suggestion and not suggestion.get('skip_reason') and not suggestion.get('blocked'):
            result['suggestions'].append(suggestion)

    return result


def get_modification_log(limit: int = 100) -> List[Dict[str, Any]]:
    """
    Get recent modification log entries.

    Args:
        limit: Maximum entries to return

    Returns:
        List of log entry dicts
    """
    conn = _init_db()

    try:
        cursor = conn.execute(
            "SELECT * FROM modification_log ORDER BY timestamp DESC LIMIT ?",
            (limit,)
        )
        return [dict(row) for row in cursor.fetchall()]
    finally:
        conn.close()


__all__ = [
    "update_preference",
    "get_preference",
    "list_preferences",
    "sync_to_user_preferences",
    "suggest_prompt_update",
    "process_learnings",
    "get_modification_log",
    "MAX_UPDATES_PER_SESSION",
    "USER_PREFERENCES_PATH",
]
