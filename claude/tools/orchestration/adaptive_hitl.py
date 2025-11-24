#!/usr/bin/env python3
"""
Adaptive Human-in-the-Loop - Agentic AI Enhancement Phase 3

Implements dynamic HITL pattern:
  CURRENT: Fixed checkpoints (always ask before delete)
  AGENTIC: Risk-assessed checkpoints (ask when uncertainty > threshold)

Key Features:
- Calculate confidence for each action
- Only pause for human when confidence < threshold
- Learn from human corrections to adjust thresholds

Author: Maia System
Created: 2025-11-24 (Agentic AI Enhancement Project - Phase 3)
"""

import json
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass


@dataclass
class ActionDecision:
    """Record of a human decision on an action"""
    action_type: str
    action_details: Dict
    approved: bool
    feedback: Optional[str]
    timestamp: datetime
    confidence_at_time: float


class AdaptiveHITL:
    """
    Adaptive Human-in-the-Loop System.

    Learns when to pause for human input based on action confidence
    and historical approval patterns.
    """

    # Base confidence by action category
    BASE_CONFIDENCE = {
        'safe': 0.95,      # Read operations
        'moderate': 0.7,   # Write operations
        'destructive': 0.4, # Delete operations
        'critical': 0.1    # Force push, drop table, etc.
    }

    # Action type to category mapping
    ACTION_CATEGORIES = {
        # Safe actions
        'file_read': 'safe',
        'list_files': 'safe',
        'search': 'safe',
        'query': 'safe',
        'get': 'safe',

        # Moderate actions
        'file_write': 'moderate',
        'file_create': 'moderate',
        'update': 'moderate',
        'insert': 'moderate',
        'git_commit': 'moderate',
        'git_push': 'moderate',

        # Destructive actions
        'file_delete': 'destructive',
        'delete': 'destructive',
        'remove': 'destructive',
        'git_reset': 'destructive',

        # Critical actions
        'git_push_force': 'critical',
        'database_drop': 'critical',
        'truncate': 'critical',
        'format': 'critical',
    }

    # Always pause for these
    ALWAYS_PAUSE = [
        'git_push_force',
        'database_drop',
        'rm_rf',
        'format_disk',
        'delete_branch_main',
        'delete_branch_master',
    ]

    def __init__(
        self,
        db_path: Optional[str] = None,
        pause_threshold: float = 0.7
    ):
        """
        Initialize Adaptive HITL System.

        Args:
            db_path: Path to SQLite database for learning
            pause_threshold: Confidence below which to pause (default: 0.7)
        """
        if db_path is None:
            maia_root = Path(__file__).resolve().parents[3]
            db_path = maia_root / "claude" / "data" / "databases" / "intelligence" / "adaptive_hitl.db"

        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.pause_threshold = pause_threshold
        self.recent_actions = []  # For rate limiting

        self._init_database()

    def _init_database(self):
        """Initialize database schema"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Table 1: Decision History
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS decisions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME NOT NULL,
                action_type TEXT NOT NULL,
                action_json TEXT,
                approved BOOLEAN NOT NULL,
                feedback TEXT,
                confidence REAL
            )
        """)

        # Table 2: Learned Confidences
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS learned_confidence (
                action_type TEXT PRIMARY KEY,
                confidence REAL DEFAULT 0.5,
                approval_count INTEGER DEFAULT 0,
                rejection_count INTEGER DEFAULT 0,
                last_updated DATETIME
            )
        """)

        # Index
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_decisions_type
            ON decisions(action_type, timestamp)
        """)

        conn.commit()
        conn.close()

    def classify_action(self, action: Dict) -> str:
        """
        Classify action into category.

        Args:
            action: Action dict with 'type' key

        Returns:
            Category: 'safe', 'moderate', 'destructive', or 'critical'
        """
        action_type = action.get('type', '').lower()

        # Direct match
        if action_type in self.ACTION_CATEGORIES:
            return self.ACTION_CATEGORIES[action_type]

        # Pattern matching
        if any(s in action_type for s in ['read', 'get', 'list', 'search', 'query']):
            return 'safe'
        elif any(s in action_type for s in ['write', 'create', 'update', 'insert']):
            return 'moderate'
        elif any(s in action_type for s in ['delete', 'remove', 'drop']):
            return 'destructive'
        elif any(s in action_type for s in ['force', 'reset_hard', 'truncate']):
            return 'critical'

        return 'moderate'  # Default to moderate

    def calculate_confidence(
        self,
        action: Dict,
        context: Optional[Dict] = None
    ) -> float:
        """
        Calculate confidence for an action.

        Args:
            action: Action to evaluate
            context: Optional context (environment, etc.)

        Returns:
            Confidence score (0.0-1.0)
        """
        # Check for explicit override
        if 'confidence_override' in action:
            return action['confidence_override']

        action_type = action.get('type', 'unknown')
        category = self.classify_action(action)

        # Base confidence from category
        confidence = self.BASE_CONFIDENCE.get(category, 0.5)

        # Adjust based on learned patterns
        learned = self.get_learned_confidence(action_type)
        if learned > 0:
            # Blend base with learned (weighted toward learned if we have data)
            confidence = confidence * 0.3 + learned * 0.7

        # Context adjustments
        if context:
            # Production environment = more cautious
            if context.get('environment') == 'production':
                confidence *= 0.7
            elif context.get('environment') == 'development':
                confidence *= 1.1

            # High-value targets = more cautious
            path = action.get('path', '')
            if any(s in path.lower() for s in ['production', 'prod', 'main', 'master']):
                confidence *= 0.8

        return min(1.0, max(0.0, confidence))

    def should_pause(self, action: Dict, context: Optional[Dict] = None) -> Tuple[bool, str]:
        """
        Determine if we should pause for human input.

        Args:
            action: Action to evaluate
            context: Optional context

        Returns:
            Tuple of (should_pause, reason)
        """
        action_type = action.get('type', 'unknown')

        # Always pause for critical actions
        if action_type in self.ALWAYS_PAUSE:
            return True, f"Critical action '{action_type}' always requires confirmation"

        # Check for bulk operations
        targets = action.get('targets', [])
        if isinstance(targets, list) and len(targets) > 3:
            return True, f"Bulk operation affecting {len(targets)} items requires confirmation"

        # Check rate limiting
        if self._is_rate_limited(action):
            return True, "Rate limit reached - pausing for confirmation"

        # Calculate confidence
        confidence = self.calculate_confidence(action, context)

        if confidence < self.pause_threshold:
            return True, f"Low confidence ({confidence:.0%}) - requesting human confirmation"

        return False, f"High confidence ({confidence:.0%}) - proceeding"

    def _is_rate_limited(self, action: Dict) -> bool:
        """Check if we've hit rate limits"""
        # Track recent actions
        now = datetime.now()
        self.recent_actions = [
            a for a in self.recent_actions
            if (now - a['timestamp']).seconds < 60
        ]

        self.recent_actions.append({
            'type': action.get('type'),
            'timestamp': now
        })

        # More than 10 actions per minute = pause
        return len(self.recent_actions) > 10

    def record_action_attempt(self, action: Dict):
        """Record an action attempt for rate limiting"""
        self.recent_actions.append({
            'type': action.get('type'),
            'timestamp': datetime.now()
        })

    def record_decision(
        self,
        action: Dict,
        approved: bool,
        human_feedback: Optional[str] = None
    ):
        """
        Record a human decision for learning.

        Args:
            action: The action that was evaluated
            approved: Whether human approved
            human_feedback: Optional feedback text
        """
        action_type = action.get('type', 'unknown')
        confidence = self.calculate_confidence(action)

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Record decision
        cursor.execute("""
            INSERT INTO decisions
            (timestamp, action_type, action_json, approved, feedback, confidence)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            datetime.now().isoformat(),
            action_type,
            json.dumps(action),
            approved,
            human_feedback,
            confidence
        ))

        # Update learned confidence (using same connection)
        self._update_learned_confidence_with_cursor(action_type, approved, cursor)

        conn.commit()
        conn.close()

    def _update_learned_confidence_with_cursor(self, action_type: str, approved: bool, cursor):
        """Update learned confidence for an action type using existing cursor"""
        # Get current stats
        cursor.execute("""
            SELECT confidence, approval_count, rejection_count
            FROM learned_confidence
            WHERE action_type = ?
        """, (action_type,))

        row = cursor.fetchone()

        if row:
            conf, approvals, rejections = row
            if approved:
                approvals += 1
            else:
                rejections += 1
        else:
            approvals = 1 if approved else 0
            rejections = 0 if approved else 1

        # Calculate new confidence
        total = approvals + rejections
        if total > 0:
            new_confidence = approvals / total
        else:
            new_confidence = 0.5

        # Save
        cursor.execute("""
            INSERT OR REPLACE INTO learned_confidence
            (action_type, confidence, approval_count, rejection_count, last_updated)
            VALUES (?, ?, ?, ?, ?)
        """, (
            action_type,
            new_confidence,
            approvals,
            rejections,
            datetime.now().isoformat()
        ))

    def get_learned_confidence(self, action_type: str) -> float:
        """Get learned confidence for an action type"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT confidence FROM learned_confidence WHERE action_type = ?
        """, (action_type,))

        row = cursor.fetchone()
        conn.close()

        return row[0] if row else 0.0

    def get_recent_decisions(self, limit: int = 50) -> List[Dict]:
        """Get recent decisions"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT timestamp, action_type, approved, feedback, confidence
            FROM decisions
            ORDER BY timestamp DESC
            LIMIT ?
        """, (limit,))

        rows = cursor.fetchall()
        conn.close()

        return [
            {
                'timestamp': r[0],
                'action_type': r[1],
                'approved': r[2],
                'feedback': r[3],
                'confidence': r[4]
            }
            for r in rows
        ]

    def get_stats(self) -> Dict[str, Any]:
        """Get HITL statistics"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                COUNT(*) as total,
                SUM(CASE WHEN approved THEN 1 ELSE 0 END) as approvals,
                SUM(CASE WHEN NOT approved THEN 1 ELSE 0 END) as rejections
            FROM decisions
        """)

        row = cursor.fetchone()
        conn.close()

        return {
            'total_decisions': row[0] or 0,
            'approvals': row[1] or 0,
            'rejections': row[2] or 0,
            'approval_rate': (row[1] / row[0] * 100) if row[0] else 0
        }


def main():
    """CLI for adaptive HITL"""
    import argparse

    parser = argparse.ArgumentParser(description="Adaptive Human-in-the-Loop")
    subparsers = parser.add_subparsers(dest='command', help='Commands')

    # Check command
    check_parser = subparsers.add_parser('check', help='Check if action needs human approval')
    check_parser.add_argument('action_type', help='Action type')
    check_parser.add_argument('--env', choices=['development', 'production'], default='development')

    # Stats command
    subparsers.add_parser('stats', help='Show HITL statistics')

    # History command
    hist_parser = subparsers.add_parser('history', help='Show decision history')
    hist_parser.add_argument('--limit', type=int, default=10)

    args = parser.parse_args()

    hitl = AdaptiveHITL()

    if args.command == 'check':
        action = {'type': args.action_type}
        context = {'environment': args.env}

        should_pause, reason = hitl.should_pause(action, context)
        confidence = hitl.calculate_confidence(action, context)

        status = "" if should_pause else ""
        print(f"{status} {reason}")
        print(f"   Confidence: {confidence:.0%}")
        print(f"   Category: {hitl.classify_action(action)}")

    elif args.command == 'stats':
        stats = hitl.get_stats()
        print("\nAdaptive HITL Statistics")
        print("=" * 40)
        print(f"Total Decisions: {stats['total_decisions']}")
        print(f"Approvals: {stats['approvals']}")
        print(f"Rejections: {stats['rejections']}")
        print(f"Approval Rate: {stats['approval_rate']:.1f}%")

    elif args.command == 'history':
        decisions = hitl.get_recent_decisions(args.limit)
        print("\nRecent Decisions")
        print("=" * 40)
        for d in decisions:
            status = "" if d['approved'] else ""
            print(f"{status} {d['action_type']} ({d['confidence']:.0%})")

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
