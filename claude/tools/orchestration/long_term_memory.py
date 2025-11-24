#!/usr/bin/env python3
"""
Long-Term Memory System - Agentic AI Enhancement Phase 2

Implements memory-enhanced agents with cross-session learning:
  CURRENT: Each session = blank slate
  AGENTIC: Sessions build on accumulated preferences/history

Key Features:
- Persist key decisions, user corrections, preferences to SQLite
- Load relevant history at session start
- Weight recent interactions higher than old
- Infer preferences from correction patterns

Author: Maia System
Created: 2025-11-24 (Agentic AI Enhancement Project - Phase 2)
"""

import json
import sqlite3
import re
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict


class LongTermMemory:
    """
    Long-Term Memory System for Cross-Session Learning.

    Persists user preferences, correction patterns, and learned behaviors
    across sessions for personalized and improving interactions.
    """

    # Decay parameters
    INFERRED_DECAY_RATE = 0.01  # Per day decay for inferred preferences
    MIN_CONFIDENCE = 0.1  # Minimum confidence before pruning
    PATTERN_THRESHOLD = 3  # Minimum occurrences to infer pattern

    def __init__(self, db_path: Optional[str] = None):
        """
        Initialize Long-Term Memory System.

        Args:
            db_path: Path to SQLite database for persistence
        """
        if db_path is None:
            maia_root = Path(__file__).resolve().parents[3]
            db_path = maia_root / "claude" / "data" / "databases" / "user" / "preferences.db"

        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        self._init_database()

    def _init_database(self):
        """Initialize database schema"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Table 1: User Preferences
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_preferences (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                preference_key TEXT UNIQUE NOT NULL,
                preference_value TEXT NOT NULL,
                confidence REAL DEFAULT 1.0,
                source TEXT DEFAULT 'explicit',
                created_at DATETIME NOT NULL,
                last_updated DATETIME NOT NULL
            )
        """)

        # Table 2: Correction Patterns
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS correction_patterns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                original_output TEXT NOT NULL,
                correction TEXT NOT NULL,
                domain TEXT,
                timestamp DATETIME NOT NULL
            )
        """)

        # Table 3: Inferred Patterns (aggregated)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS inferred_patterns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                pattern_key TEXT UNIQUE NOT NULL,
                pattern_description TEXT,
                occurrence_count INTEGER DEFAULT 1,
                confidence REAL DEFAULT 0.5,
                last_seen DATETIME NOT NULL
            )
        """)

        # Indexes
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_pref_key
            ON user_preferences(preference_key)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_corrections_domain
            ON correction_patterns(domain, timestamp)
        """)

        conn.commit()
        conn.close()

    def store_preference(
        self,
        key: str,
        value: str,
        source: str = "explicit",
        confidence: float = 1.0
    ):
        """
        Store a user preference.

        Args:
            key: Preference key (e.g., "preferred_language", "sre.monitoring")
            value: Preference value
            source: "explicit" (user stated) or "inferred" (learned)
            confidence: Confidence level (0.0-1.0)
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        now = datetime.now().isoformat()

        cursor.execute("""
            INSERT INTO user_preferences
            (preference_key, preference_value, confidence, source, created_at, last_updated)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(preference_key) DO UPDATE SET
                preference_value = excluded.preference_value,
                confidence = excluded.confidence,
                source = excluded.source,
                last_updated = excluded.last_updated
        """, (key, value, confidence, source, now, now))

        conn.commit()
        conn.close()

    def get_preference(self, key: str) -> Optional[Dict[str, Any]]:
        """
        Get a user preference.

        Args:
            key: Preference key

        Returns:
            Dict with preference details or None
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT preference_key, preference_value, confidence, source, created_at, last_updated
            FROM user_preferences
            WHERE preference_key = ?
        """, (key,))

        row = cursor.fetchone()
        conn.close()

        if row:
            return {
                'key': row[0],
                'value': row[1],
                'confidence': row[2],
                'source': row[3],
                'created_at': row[4],
                'last_updated': row[5]
            }
        return None

    def get_domain_preferences(self, domain: str) -> List[Dict[str, Any]]:
        """
        Get all preferences for a domain.

        Args:
            domain: Domain prefix (e.g., "sre" matches "sre.monitoring", "sre.alerting")

        Returns:
            List of preference dicts
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT preference_key, preference_value, confidence, source
            FROM user_preferences
            WHERE preference_key LIKE ?
        """, (f"{domain}.%",))

        rows = cursor.fetchall()
        conn.close()

        return [
            {'key': r[0], 'value': r[1], 'confidence': r[2], 'source': r[3]}
            for r in rows
        ]

    def get_preferences_above_confidence(self, min_confidence: float) -> List[Dict[str, Any]]:
        """Get preferences above a confidence threshold"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT preference_key, preference_value, confidence, source
            FROM user_preferences
            WHERE confidence >= ?
            ORDER BY confidence DESC
        """, (min_confidence,))

        rows = cursor.fetchall()
        conn.close()

        return [
            {'key': r[0], 'value': r[1], 'confidence': r[2], 'source': r[3]}
            for r in rows
        ]

    def clear_preference(self, key: str):
        """Clear a specific preference"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("DELETE FROM user_preferences WHERE preference_key = ?", (key,))

        conn.commit()
        conn.close()

    def get_decayed_confidence(self, key: str, days_old: int = None) -> float:
        """
        Get confidence with time decay applied.

        Args:
            key: Preference key
            days_old: Override days for testing

        Returns:
            Decayed confidence value
        """
        pref = self.get_preference(key)
        if not pref:
            return 0.0

        if pref['source'] == 'explicit':
            # Explicit preferences don't decay
            return pref['confidence']

        # Calculate days since last update
        if days_old is not None:
            days = days_old
        else:
            last_updated = datetime.fromisoformat(pref['last_updated'])
            days = (datetime.now() - last_updated).days

        # Apply decay
        decayed = pref['confidence'] * (1 - self.INFERRED_DECAY_RATE * days)
        return max(self.MIN_CONFIDENCE, decayed)

    def record_correction(self, original_output: str, correction: str, domain: str = None):
        """
        Record a user correction for pattern learning.

        Args:
            original_output: What was originally output
            correction: What the user corrected it to
            domain: Task domain (optional)
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO correction_patterns
            (original_output, correction, domain, timestamp)
            VALUES (?, ?, ?, ?)
        """, (
            original_output[:500],  # Truncate to reasonable size
            correction[:500],
            domain,
            datetime.now().isoformat()
        ))

        conn.commit()
        conn.close()

    def get_correction_patterns(self, domain: str = None, limit: int = 50) -> List[Dict]:
        """Get recent correction patterns"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        if domain:
            cursor.execute("""
                SELECT original_output, correction, domain, timestamp
                FROM correction_patterns
                WHERE domain = ?
                ORDER BY timestamp DESC
                LIMIT ?
            """, (domain, limit))
        else:
            cursor.execute("""
                SELECT original_output, correction, domain, timestamp
                FROM correction_patterns
                ORDER BY timestamp DESC
                LIMIT ?
            """, (limit,))

        rows = cursor.fetchall()
        conn.close()

        return [
            {'original': r[0], 'correction': r[1], 'domain': r[2], 'timestamp': r[3]}
            for r in rows
        ]

    def infer_preferences_from_corrections(self) -> List[Dict]:
        """
        Analyze corrections to infer preferences.

        Returns:
            List of inferred preference suggestions
        """
        corrections = self.get_correction_patterns(limit=100)

        if not corrections:
            return []

        # Simple pattern detection - look for repeated words in corrections
        correction_words = {}
        for c in corrections:
            words = re.findall(r'\b\w+\b', c['correction'].lower())
            for word in words:
                if len(word) > 3:  # Skip short words
                    correction_words[word] = correction_words.get(word, 0) + 1

        # Find frequently mentioned words
        inferred = []
        for word, count in correction_words.items():
            if count >= self.PATTERN_THRESHOLD:
                inferred.append({
                    'pattern': f"User frequently mentions '{word}' in corrections",
                    'count': count,
                    'confidence': min(0.9, 0.3 + (count * 0.1))
                })

        return inferred

    def analyze_correction_patterns(self) -> List[Dict]:
        """
        Analyze correction patterns for insights.

        Returns:
            List of pattern insights
        """
        return self.infer_preferences_from_corrections()

    def load_session_context(self) -> Dict[str, Any]:
        """
        Load relevant context for session startup.

        Returns:
            Dict with preferences and relevant history
        """
        # Get high-confidence preferences
        high_conf_prefs = self.get_preferences_above_confidence(0.7)

        # Get recent corrections for awareness
        recent_corrections = self.get_correction_patterns(limit=10)

        # Get inferred patterns
        inferred = self.infer_preferences_from_corrections()

        return {
            'preferences': high_conf_prefs,
            'recent_corrections': recent_corrections,
            'inferred_patterns': inferred,
            'loaded_at': datetime.now().isoformat()
        }

    def export_all(self) -> Dict[str, Any]:
        """Export all memory data"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Get all preferences
        cursor.execute("""
            SELECT preference_key, preference_value, confidence, source, last_updated
            FROM user_preferences
            ORDER BY preference_key
        """)
        prefs = [
            {'key': r[0], 'value': r[1], 'confidence': r[2], 'source': r[3], 'updated': r[4]}
            for r in cursor.fetchall()
        ]

        # Get correction count by domain
        cursor.execute("""
            SELECT domain, COUNT(*) as cnt
            FROM correction_patterns
            GROUP BY domain
        """)
        corrections = {r[0] or 'general': r[1] for r in cursor.fetchall()}

        conn.close()

        return {
            'preferences': prefs,
            'corrections': corrections,
            'exported_at': datetime.now().isoformat()
        }


def main():
    """CLI for long-term memory system"""
    import argparse

    parser = argparse.ArgumentParser(description="Long-Term Memory System")
    subparsers = parser.add_subparsers(dest='command', help='Commands')

    # Get command
    get_parser = subparsers.add_parser('get', help='Get a preference')
    get_parser.add_argument('key', help='Preference key')

    # Set command
    set_parser = subparsers.add_parser('set', help='Set a preference')
    set_parser.add_argument('key', help='Preference key')
    set_parser.add_argument('value', help='Preference value')
    set_parser.add_argument('--confidence', type=float, default=1.0)

    # List command
    list_parser = subparsers.add_parser('list', help='List preferences')
    list_parser.add_argument('--domain', '-d', help='Filter by domain')
    list_parser.add_argument('--json', action='store_true')

    # Context command
    subparsers.add_parser('context', help='Load session context')

    # Export command
    subparsers.add_parser('export', help='Export all data')

    args = parser.parse_args()

    memory = LongTermMemory()

    if args.command == 'get':
        pref = memory.get_preference(args.key)
        if pref:
            print(f"{args.key} = {pref['value']} (confidence: {pref['confidence']:.0%})")
        else:
            print(f"Preference '{args.key}' not found")

    elif args.command == 'set':
        memory.store_preference(args.key, args.value, "explicit", args.confidence)
        print(f"✅ Set {args.key} = {args.value}")

    elif args.command == 'list':
        if args.domain:
            prefs = memory.get_domain_preferences(args.domain)
        else:
            prefs = memory.get_preferences_above_confidence(0.0)

        if args.json:
            print(json.dumps(prefs, indent=2))
        else:
            print("\n📋 Preferences")
            print("=" * 40)
            for p in prefs:
                print(f"  {p['key']}: {p['value']} ({p['confidence']:.0%})")

    elif args.command == 'context':
        context = memory.load_session_context()
        print("\n🧠 Session Context")
        print("=" * 40)
        print(f"Preferences: {len(context['preferences'])}")
        print(f"Recent Corrections: {len(context['recent_corrections'])}")
        print(f"Inferred Patterns: {len(context['inferred_patterns'])}")

    elif args.command == 'export':
        export = memory.export_all()
        print(json.dumps(export, indent=2))

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
