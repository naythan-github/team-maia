#!/usr/bin/env python3
"""
Routing Decision Logger - Phase 122

Logs routing suggestions from coordinator and tracks actual agent usage
to measure routing accuracy and acceptance rates.

Usage:
    # Log routing suggestion
    logger = RoutingDecisionLogger()
    logger.log_suggestion(query, intent, routing)

    # Log actual agent usage (later in conversation)
    logger.log_actual_usage(query_hash, agents_used, accepted=True)

    # Get recent decisions
    decisions = logger.get_recent_decisions(limit=100)

Database: routing_decisions.db
Tables: routing_suggestions, acceptance_tracking, override_patterns
"""

import sqlite3
import hashlib
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict


@dataclass
class RoutingIntent:
    """Intent classification result"""
    category: str
    domains: List[str]
    complexity: int  # 1-10
    confidence: float  # 0.0-1.0


@dataclass
class RoutingDecision:
    """Routing decision from coordinator"""
    agents: List[str]
    initial_agent: str
    strategy: str  # single_agent, swarm, prompt_chain
    reasoning: str
    confidence: float


@dataclass
class RoutingSuggestion:
    """Complete routing suggestion record"""
    query_hash: str
    timestamp: datetime
    query_text: str
    query_category: str
    query_complexity: int

    # Routing suggestion
    suggested_agents: List[str]
    initial_agent: str
    routing_strategy: str
    reasoning: str
    confidence: float

    # Acceptance tracking (filled later)
    accepted: Optional[bool] = None
    actual_agents: Optional[List[str]] = None
    override_reason: Optional[str] = None
    acceptance_timestamp: Optional[datetime] = None


class RoutingDecisionLogger:
    """Logs routing decisions and tracks acceptance"""

    def __init__(self, db_path: Optional[str] = None):
        """
        Initialize logger.

        Args:
            db_path: Path to SQLite database (default: claude/data/routing_decisions.db)
        """
        if db_path is None:
            maia_root = Path(__file__).resolve().parents[3]
            db_path = maia_root / "claude" / "data" / "routing_decisions.db"

        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        self._init_database()

    def _init_database(self):
        """Initialize database schema"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Table 1: Routing Suggestions (logged when coordinator suggests agents)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS routing_suggestions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                query_hash TEXT NOT NULL,
                timestamp DATETIME NOT NULL,

                -- Query context
                query_text TEXT,
                query_category TEXT,
                query_complexity INTEGER,

                -- Routing suggestion
                suggested_agents TEXT,  -- JSON array
                initial_agent TEXT,
                routing_strategy TEXT,
                reasoning TEXT,
                confidence FLOAT,

                -- Acceptance tracking (populated later)
                accepted BOOLEAN,
                actual_agents TEXT,  -- JSON array
                override_reason TEXT,
                acceptance_timestamp DATETIME,

                UNIQUE(query_hash, timestamp)
            )
        """)

        # Table 2: Acceptance Tracking (aggregated metrics)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS acceptance_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date DATE NOT NULL,
                category TEXT,

                -- Acceptance rates
                total_suggestions INTEGER DEFAULT 0,
                accepted_count INTEGER DEFAULT 0,
                rejected_count INTEGER DEFAULT 0,
                partial_count INTEGER DEFAULT 0,  -- Some agents used, not all

                -- Accuracy metrics
                acceptance_rate FLOAT,
                avg_confidence FLOAT,

                UNIQUE(date, category)
            )
        """)

        # Table 3: Override Patterns (why Maia overrides routing)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS override_patterns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME NOT NULL,
                query_hash TEXT,

                -- Suggestion vs actual
                suggested_agents TEXT,  -- JSON
                actual_agents TEXT,  -- JSON

                -- Override analysis
                override_type TEXT,  -- full_reject, partial_accept, agent_substitution
                override_reason TEXT,
                category TEXT,
                complexity INTEGER,

                -- Context
                confidence FLOAT,
                context_notes TEXT
            )
        """)

        # Indexes for performance
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_query_hash ON routing_suggestions(query_hash)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_timestamp ON routing_suggestions(timestamp)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_accepted ON routing_suggestions(accepted)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_category ON routing_suggestions(query_category)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_date_category ON acceptance_metrics(date, category)")

        conn.commit()
        conn.close()

    def _hash_query(self, query: str) -> str:
        """Generate hash for query (for linking suggestion to actual usage)"""
        return hashlib.sha256(query.encode()).hexdigest()[:16]

    def log_suggestion(
        self,
        query: str,
        intent: RoutingIntent,
        routing: RoutingDecision
    ) -> str:
        """
        Log routing suggestion from coordinator.

        Args:
            query: User query text
            intent: Intent classification result
            routing: Routing decision

        Returns:
            query_hash: Hash for tracking actual usage later
        """
        query_hash = self._hash_query(query)
        timestamp = datetime.now()

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute("""
                INSERT INTO routing_suggestions (
                    query_hash, timestamp,
                    query_text, query_category, query_complexity,
                    suggested_agents, initial_agent, routing_strategy,
                    reasoning, confidence
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                query_hash, timestamp,
                query[:500],  # Truncate long queries
                intent.category,
                intent.complexity,
                json.dumps(routing.agents),
                routing.initial_agent,
                routing.strategy,
                routing.reasoning,
                routing.confidence
            ))

            conn.commit()
            return query_hash

        except sqlite3.IntegrityError:
            # Duplicate - query already logged at this exact timestamp
            pass
        finally:
            conn.close()

        return query_hash

    def log_actual_usage(
        self,
        query_hash: str,
        actual_agents: List[str],
        accepted: bool,
        override_reason: Optional[str] = None
    ):
        """
        Log actual agent usage after conversation completes.

        Args:
            query_hash: Hash from log_suggestion()
            actual_agents: Agents actually used by Maia
            accepted: Whether routing suggestion was accepted
            override_reason: Why routing was overridden (if rejected)
        """
        timestamp = datetime.now()

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Update routing_suggestions with actual usage
        cursor.execute("""
            UPDATE routing_suggestions
            SET accepted = ?,
                actual_agents = ?,
                override_reason = ?,
                acceptance_timestamp = ?
            WHERE query_hash = ?
            AND acceptance_timestamp IS NULL
            ORDER BY timestamp DESC
            LIMIT 1
        """, (
            accepted,
            json.dumps(actual_agents),
            override_reason,
            timestamp,
            query_hash
        ))

        # If rejected, log override pattern
        if not accepted:
            cursor.execute("""
                SELECT suggested_agents, query_category, query_complexity, confidence
                FROM routing_suggestions
                WHERE query_hash = ?
                ORDER BY timestamp DESC
                LIMIT 1
            """, (query_hash,))

            row = cursor.fetchone()
            if row:
                suggested_agents, category, complexity, confidence = row

                # Determine override type
                suggested = set(json.loads(suggested_agents))
                actual = set(actual_agents)

                if len(actual & suggested) == 0:
                    override_type = "full_reject"
                elif len(actual & suggested) < len(suggested):
                    override_type = "partial_accept"
                else:
                    override_type = "agent_substitution"

                cursor.execute("""
                    INSERT INTO override_patterns (
                        timestamp, query_hash,
                        suggested_agents, actual_agents,
                        override_type, override_reason,
                        category, complexity, confidence
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    timestamp, query_hash,
                    suggested_agents, json.dumps(actual_agents),
                    override_type, override_reason,
                    category, complexity, confidence
                ))

        conn.commit()
        conn.close()

    def update_acceptance_metrics(self, date: Optional[datetime] = None):
        """
        Calculate and update acceptance metrics for a date.

        Args:
            date: Date to calculate metrics for (default: today)
        """
        if date is None:
            date = datetime.now().date()

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Get categories with data for this date
        cursor.execute("""
            SELECT DISTINCT query_category
            FROM routing_suggestions
            WHERE DATE(timestamp) = ?
            AND accepted IS NOT NULL
        """, (date,))

        categories = [row[0] for row in cursor.fetchall()]

        # Calculate metrics for each category
        for category in categories:
            cursor.execute("""
                SELECT
                    COUNT(*) as total,
                    SUM(CASE WHEN accepted = 1 THEN 1 ELSE 0 END) as accepted,
                    SUM(CASE WHEN accepted = 0 THEN 1 ELSE 0 END) as rejected,
                    AVG(confidence) as avg_confidence
                FROM routing_suggestions
                WHERE DATE(timestamp) = ?
                AND query_category = ?
                AND accepted IS NOT NULL
            """, (date, category))

            row = cursor.fetchone()
            if row and row[0] > 0:
                total, accepted, rejected, avg_confidence = row
                acceptance_rate = accepted / total if total > 0 else 0.0

                # Insert or update metrics
                cursor.execute("""
                    INSERT INTO acceptance_metrics (
                        date, category,
                        total_suggestions, accepted_count, rejected_count,
                        acceptance_rate, avg_confidence
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(date, category) DO UPDATE SET
                        total_suggestions = excluded.total_suggestions,
                        accepted_count = excluded.accepted_count,
                        rejected_count = excluded.rejected_count,
                        acceptance_rate = excluded.acceptance_rate,
                        avg_confidence = excluded.avg_confidence
                """, (
                    date, category,
                    total, accepted, rejected,
                    acceptance_rate, avg_confidence
                ))

        conn.commit()
        conn.close()

    def get_recent_decisions(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get recent routing decisions"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                query_hash, timestamp, query_text, query_category, query_complexity,
                suggested_agents, initial_agent, routing_strategy, reasoning, confidence,
                accepted, actual_agents, override_reason, acceptance_timestamp
            FROM routing_suggestions
            ORDER BY timestamp DESC
            LIMIT ?
        """, (limit,))

        decisions = []
        for row in cursor.fetchall():
            decisions.append({
                'query_hash': row[0],
                'timestamp': row[1],
                'query_text': row[2],
                'query_category': row[3],
                'query_complexity': row[4],
                'suggested_agents': json.loads(row[5]) if row[5] else [],
                'initial_agent': row[6],
                'routing_strategy': row[7],
                'reasoning': row[8],
                'confidence': row[9],
                'accepted': row[10],
                'actual_agents': json.loads(row[11]) if row[11] else [],
                'override_reason': row[12],
                'acceptance_timestamp': row[13]
            })

        conn.close()
        return decisions

    def get_acceptance_rate(
        self,
        category: Optional[str] = None,
        days: int = 7
    ) -> float:
        """
        Get acceptance rate for a category over recent days.

        Args:
            category: Category to filter by (None = all)
            days: Number of days to look back

        Returns:
            Acceptance rate (0.0-1.0)
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cutoff = datetime.now() - timedelta(days=days)

        if category:
            cursor.execute("""
                SELECT
                    COUNT(*) as total,
                    SUM(CASE WHEN accepted = 1 THEN 1 ELSE 0 END) as accepted
                FROM routing_suggestions
                WHERE timestamp >= ?
                AND query_category = ?
                AND accepted IS NOT NULL
            """, (cutoff, category))
        else:
            cursor.execute("""
                SELECT
                    COUNT(*) as total,
                    SUM(CASE WHEN accepted = 1 THEN 1 ELSE 0 END) as accepted
                FROM routing_suggestions
                WHERE timestamp >= ?
                AND accepted IS NOT NULL
            """, (cutoff,))

        row = cursor.fetchone()
        conn.close()

        if row and row[0] > 0:
            return row[1] / row[0]
        return 0.0


def main():
    """CLI interface for testing"""
    import sys

    if len(sys.argv) < 2:
        print("Usage:")
        print("  routing_decision_logger.py test        # Run test logging")
        print("  routing_decision_logger.py stats       # Show statistics")
        print("  routing_decision_logger.py recent [N]  # Show recent N decisions")
        sys.exit(1)

    logger = RoutingDecisionLogger()

    if sys.argv[1] == "test":
        # Test logging
        intent = RoutingIntent(
            category="technical",
            domains=["azure", "infrastructure"],
            complexity=7,
            confidence=0.85
        )

        routing = RoutingDecision(
            agents=["Azure Solutions Architect Agent", "SRE Principal Engineer Agent"],
            initial_agent="Azure Solutions Architect Agent",
            strategy="swarm",
            reasoning="Complex Azure infrastructure query requiring both architecture and SRE expertise",
            confidence=0.85
        )

        query = "Help me optimize Azure costs for compute resources"
        query_hash = logger.log_suggestion(query, intent, routing)
        print(f"✅ Logged routing suggestion: {query_hash}")

        # Simulate acceptance
        logger.log_actual_usage(
            query_hash,
            actual_agents=["Azure Solutions Architect Agent"],
            accepted=False,
            override_reason="User context suggested single agent sufficient"
        )
        print("✅ Logged actual usage (override)")

        # Update metrics
        logger.update_acceptance_metrics()
        print("✅ Updated acceptance metrics")

    elif sys.argv[1] == "stats":
        # Show statistics
        rate_7d = logger.get_acceptance_rate(days=7)
        rate_30d = logger.get_acceptance_rate(days=30)

        print(f"📊 Routing Acceptance Statistics")
        print(f"  Last 7 days:  {rate_7d:.1%}")
        print(f"  Last 30 days: {rate_30d:.1%}")

    elif sys.argv[1] == "recent":
        # Show recent decisions
        limit = int(sys.argv[2]) if len(sys.argv) > 2 else 10
        decisions = logger.get_recent_decisions(limit=limit)

        print(f"📋 Recent {len(decisions)} Routing Decisions\n")
        for d in decisions:
            accepted = "✅" if d['accepted'] else "❌" if d['accepted'] is False else "⏳"
            print(f"{accepted} {d['timestamp']}")
            print(f"   Query: {d['query_text'][:80]}...")
            print(f"   Suggested: {', '.join(d['suggested_agents'])}")
            if d['accepted'] is not None:
                print(f"   Actual: {', '.join(d['actual_agents'])}")
            print()


if __name__ == "__main__":
    main()
