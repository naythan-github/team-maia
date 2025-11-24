#!/usr/bin/env python3
"""
Outcome Tracking Database - Agentic AI Enhancement Phase 4 (Phase 181)

Unified outcome tracking to enable:
- A/B testing of different approaches
- Speculative execution path selection
- Pattern success rate analytics
- Continuous improvement feedback loops

Author: Maia System (SRE Principal Engineer Agent)
Created: 2025-11-24 (Agentic AI Enhancement Project - Phase 4)
"""

import json
import sqlite3
import hashlib
import logging
import threading
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict, field
from contextlib import contextmanager
import uuid

# Configure logging
logger = logging.getLogger(__name__)


@dataclass
class Outcome:
    """Record of an agentic decision outcome"""
    domain: str
    approach: str
    success: bool
    id: Optional[str] = None
    timestamp: Optional[datetime] = None
    task_type: Optional[str] = None
    query_hash: Optional[str] = None
    variant_id: Optional[str] = None
    agent_used: Optional[str] = None
    quality_score: Optional[float] = None
    latency_ms: Optional[int] = None
    error_type: Optional[str] = None
    user_rating: Optional[int] = None
    user_correction: bool = False
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class ApproachStats:
    """Statistics for an approach"""
    approach: str
    total_count: int
    success_count: int
    success_rate: float
    avg_quality: Optional[float] = None
    avg_latency_ms: Optional[float] = None


@dataclass
class TrendPoint:
    """A data point in a trend series"""
    period: str
    success_rate: float
    total_count: int
    avg_quality: Optional[float] = None


@dataclass
class Experiment:
    """A/B testing experiment"""
    name: str
    variants: List[str]
    id: Optional[str] = None
    description: Optional[str] = None
    success_metric: str = 'success_rate'
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class ExperimentResults:
    """Results of an A/B experiment"""
    experiment_id: str
    name: str
    status: str
    variant_stats: Dict[str, ApproachStats]
    winner: Optional[str] = None
    confidence: Optional[float] = None


class OutcomeTracker:
    """
    Outcome Tracking Database for Agentic AI patterns.

    Provides unified storage for decision outcomes, enabling:
    - A/B testing comparisons
    - Pattern success rate analysis
    - Trend monitoring
    - Cross-pattern learning
    """

    def __init__(self, db_path: Optional[str] = None):
        """
        Initialize Outcome Tracker.

        Args:
            db_path: Path to SQLite database. Uses default if not provided.
        """
        if db_path is None:
            maia_root = Path(__file__).resolve().parents[3]
            db_path = maia_root / "claude" / "data" / "databases" / "intelligence" / "outcome_tracker.db"

        self.db_path = Path(db_path)
        self._local = threading.local()
        self._init_database()

    @property
    def _conn(self) -> sqlite3.Connection:
        """Get thread-local database connection"""
        if not hasattr(self._local, 'conn') or self._local.conn is None:
            self._local.conn = sqlite3.connect(
                str(self.db_path),
                timeout=30.0,
                check_same_thread=False
            )
            self._local.conn.row_factory = sqlite3.Row
            # Enable WAL mode for better concurrency
            self._local.conn.execute("PRAGMA journal_mode=WAL")
            self._local.conn.execute("PRAGMA synchronous=NORMAL")
        return self._local.conn

    @contextmanager
    def _transaction(self):
        """Context manager for database transactions"""
        conn = self._conn
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            logger.error(f"Database transaction failed: {e}")
            raise

    def _init_database(self):
        """Initialize database schema"""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        with self._transaction() as conn:
            # Outcomes table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS outcomes (
                    id TEXT PRIMARY KEY,
                    timestamp TEXT NOT NULL,
                    domain TEXT NOT NULL,
                    task_type TEXT,
                    query_hash TEXT,
                    approach TEXT NOT NULL,
                    variant_id TEXT,
                    agent_used TEXT,
                    success INTEGER NOT NULL,
                    quality_score REAL,
                    latency_ms INTEGER,
                    error_type TEXT,
                    user_rating INTEGER,
                    user_correction INTEGER DEFAULT 0,
                    metadata TEXT
                )
            """)

            # Experiments table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS experiments (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    description TEXT,
                    start_time TEXT NOT NULL,
                    end_time TEXT,
                    status TEXT DEFAULT 'active',
                    variants TEXT NOT NULL,
                    success_metric TEXT DEFAULT 'success_rate',
                    winner TEXT,
                    metadata TEXT
                )
            """)

            # Create indexes
            conn.execute("CREATE INDEX IF NOT EXISTS idx_outcomes_timestamp ON outcomes(timestamp)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_outcomes_domain ON outcomes(domain)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_outcomes_approach ON outcomes(approach)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_outcomes_variant ON outcomes(variant_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_experiments_status ON experiments(status)")

    def _validate_outcome(self, outcome: Outcome) -> None:
        """Validate outcome data"""
        if outcome.quality_score is not None:
            if not 0.0 <= outcome.quality_score <= 1.0:
                raise ValueError(f"quality_score must be between 0.0 and 1.0, got {outcome.quality_score}")

        if outcome.user_rating is not None:
            if not 1 <= outcome.user_rating <= 5:
                raise ValueError(f"user_rating must be between 1 and 5, got {outcome.user_rating}")

    def record_outcome(self, outcome: Outcome) -> str:
        """
        Record a single outcome.

        Args:
            outcome: Outcome to record

        Returns:
            The outcome ID (auto-generated if not provided)
        """
        self._validate_outcome(outcome)

        outcome_id = outcome.id or str(uuid.uuid4())
        timestamp = outcome.timestamp or datetime.now()

        with self._transaction() as conn:
            conn.execute("""
                INSERT INTO outcomes (
                    id, timestamp, domain, task_type, query_hash, approach,
                    variant_id, agent_used, success, quality_score, latency_ms,
                    error_type, user_rating, user_correction, metadata
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                outcome_id,
                timestamp.isoformat(),
                outcome.domain,
                outcome.task_type,
                outcome.query_hash,
                outcome.approach,
                outcome.variant_id,
                outcome.agent_used,
                1 if outcome.success else 0,
                outcome.quality_score,
                outcome.latency_ms,
                outcome.error_type,
                outcome.user_rating,
                1 if outcome.user_correction else 0,
                json.dumps(outcome.metadata) if outcome.metadata else None
            ))

        return outcome_id

    def record_batch(self, outcomes: List[Outcome]) -> List[str]:
        """
        Record multiple outcomes in a batch.

        Args:
            outcomes: List of outcomes to record

        Returns:
            List of outcome IDs
        """
        ids = []
        for outcome in outcomes:
            outcome_id = self.record_outcome(outcome)
            ids.append(outcome_id)
        return ids

    def get_outcome(self, outcome_id: str) -> Optional[Outcome]:
        """
        Retrieve an outcome by ID.

        Args:
            outcome_id: The outcome ID

        Returns:
            Outcome if found, None otherwise
        """
        cursor = self._conn.execute(
            "SELECT * FROM outcomes WHERE id = ?",
            (outcome_id,)
        )
        row = cursor.fetchone()

        if row is None:
            return None

        return self._row_to_outcome(row)

    def _row_to_outcome(self, row: sqlite3.Row) -> Outcome:
        """Convert database row to Outcome object"""
        return Outcome(
            id=row['id'],
            timestamp=datetime.fromisoformat(row['timestamp']),
            domain=row['domain'],
            task_type=row['task_type'],
            query_hash=row['query_hash'],
            approach=row['approach'],
            variant_id=row['variant_id'],
            agent_used=row['agent_used'],
            success=bool(row['success']),
            quality_score=row['quality_score'],
            latency_ms=row['latency_ms'],
            error_type=row['error_type'],
            user_rating=row['user_rating'],
            user_correction=bool(row['user_correction']),
            metadata=json.loads(row['metadata']) if row['metadata'] else None
        )

    def query_outcomes(
        self,
        domain: Optional[str] = None,
        approach: Optional[str] = None,
        variant_id: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 100
    ) -> List[Outcome]:
        """
        Query outcomes with optional filters.

        Args:
            domain: Filter by domain
            approach: Filter by approach
            variant_id: Filter by variant ID
            start_time: Filter by start time
            end_time: Filter by end time
            limit: Maximum results to return

        Returns:
            List of matching outcomes
        """
        query = "SELECT * FROM outcomes WHERE 1=1"
        params = []

        if domain is not None:
            query += " AND domain = ?"
            params.append(domain)

        if approach is not None:
            query += " AND approach = ?"
            params.append(approach)

        if variant_id is not None:
            query += " AND variant_id = ?"
            params.append(variant_id)

        if start_time is not None:
            query += " AND timestamp >= ?"
            params.append(start_time.isoformat())

        if end_time is not None:
            query += " AND timestamp <= ?"
            params.append(end_time.isoformat())

        query += " ORDER BY timestamp DESC LIMIT ?"
        params.append(limit)

        cursor = self._conn.execute(query, params)
        return [self._row_to_outcome(row) for row in cursor.fetchall()]

    def get_success_rate(
        self,
        domain: Optional[str] = None,
        approach: Optional[str] = None,
        days: int = 30
    ) -> float:
        """
        Calculate success rate for given filters.

        Args:
            domain: Filter by domain
            approach: Filter by approach
            days: Look back period in days

        Returns:
            Success rate (0.0 to 1.0), or 0.0 if no data
        """
        query = """
            SELECT
                COUNT(*) as total,
                SUM(success) as successes
            FROM outcomes
            WHERE timestamp >= ?
        """
        params = [(datetime.now() - timedelta(days=days)).isoformat()]

        if domain is not None:
            query += " AND domain = ?"
            params.append(domain)

        if approach is not None:
            query += " AND approach = ?"
            params.append(approach)

        cursor = self._conn.execute(query, params)
        row = cursor.fetchone()

        if row['total'] == 0:
            return 0.0

        return row['successes'] / row['total']

    def get_approach_comparison(
        self,
        approaches: List[str],
        domain: Optional[str] = None,
        days: int = 30
    ) -> Dict[str, ApproachStats]:
        """
        Compare multiple approaches.

        Args:
            approaches: List of approaches to compare
            domain: Optional domain filter
            days: Look back period

        Returns:
            Dict mapping approach to stats
        """
        results = {}
        cutoff = (datetime.now() - timedelta(days=days)).isoformat()

        for approach in approaches:
            query = """
                SELECT
                    COUNT(*) as total,
                    SUM(success) as successes,
                    AVG(quality_score) as avg_quality,
                    AVG(latency_ms) as avg_latency
                FROM outcomes
                WHERE approach = ? AND timestamp >= ?
            """
            params = [approach, cutoff]

            if domain is not None:
                query += " AND domain = ?"
                params.append(domain)

            cursor = self._conn.execute(query, params)
            row = cursor.fetchone()

            total = row['total'] or 0
            successes = row['successes'] or 0

            results[approach] = ApproachStats(
                approach=approach,
                total_count=total,
                success_count=successes,
                success_rate=successes / total if total > 0 else 0.0,
                avg_quality=row['avg_quality'],
                avg_latency_ms=row['avg_latency']
            )

        return results

    def get_trends(
        self,
        domain: Optional[str] = None,
        granularity: str = 'day',
        days: int = 30
    ) -> List[TrendPoint]:
        """
        Get success rate trends over time.

        Args:
            domain: Optional domain filter
            granularity: 'day' or 'week'
            days: Look back period

        Returns:
            List of trend points
        """
        cutoff = (datetime.now() - timedelta(days=days)).isoformat()

        if granularity == 'week':
            date_format = "strftime('%Y-W%W', timestamp)"
        else:
            date_format = "date(timestamp)"

        query = f"""
            SELECT
                {date_format} as period,
                COUNT(*) as total,
                SUM(success) as successes,
                AVG(quality_score) as avg_quality
            FROM outcomes
            WHERE timestamp >= ?
        """
        params = [cutoff]

        if domain is not None:
            query += " AND domain = ?"
            params.append(domain)

        query += f" GROUP BY {date_format} ORDER BY period"

        cursor = self._conn.execute(query, params)
        trends = []

        for row in cursor.fetchall():
            total = row['total'] or 0
            successes = row['successes'] or 0

            trends.append(TrendPoint(
                period=row['period'],
                total_count=total,
                success_rate=successes / total if total > 0 else 0.0,
                avg_quality=row['avg_quality']
            ))

        return trends

    def create_experiment(self, experiment: Experiment) -> str:
        """
        Create an A/B testing experiment.

        Args:
            experiment: Experiment configuration

        Returns:
            Experiment ID
        """
        exp_id = experiment.id or str(uuid.uuid4())

        with self._transaction() as conn:
            conn.execute("""
                INSERT INTO experiments (
                    id, name, description, start_time, status,
                    variants, success_metric, metadata
                ) VALUES (?, ?, ?, ?, 'active', ?, ?, ?)
            """, (
                exp_id,
                experiment.name,
                experiment.description,
                datetime.now().isoformat(),
                json.dumps(experiment.variants),
                experiment.success_metric,
                json.dumps(experiment.metadata) if experiment.metadata else None
            ))

        return exp_id

    def get_experiment_results(self, experiment_id: str) -> ExperimentResults:
        """
        Get results for an experiment.

        Args:
            experiment_id: The experiment ID

        Returns:
            Experiment results with per-variant stats
        """
        cursor = self._conn.execute(
            "SELECT * FROM experiments WHERE id = ?",
            (experiment_id,)
        )
        row = cursor.fetchone()

        if row is None:
            raise ValueError(f"Experiment {experiment_id} not found")

        variants = json.loads(row['variants'])
        variant_stats = {}

        for variant in variants:
            cursor = self._conn.execute("""
                SELECT
                    COUNT(*) as total,
                    SUM(success) as successes,
                    AVG(quality_score) as avg_quality,
                    AVG(latency_ms) as avg_latency
                FROM outcomes
                WHERE variant_id = ?
            """, (variant,))
            stat_row = cursor.fetchone()

            total = stat_row['total'] or 0
            successes = stat_row['successes'] or 0

            variant_stats[variant] = ApproachStats(
                approach=variant,
                total_count=total,
                success_count=successes,
                success_rate=successes / total if total > 0 else 0.0,
                avg_quality=stat_row['avg_quality'],
                avg_latency_ms=stat_row['avg_latency']
            )

        return ExperimentResults(
            experiment_id=experiment_id,
            name=row['name'],
            status=row['status'],
            variant_stats=variant_stats,
            winner=row['winner']
        )

    def end_experiment(self, experiment_id: str, winner: Optional[str] = None) -> None:
        """
        End an experiment and optionally declare a winner.

        Args:
            experiment_id: The experiment ID
            winner: Optional winner variant
        """
        with self._transaction() as conn:
            conn.execute("""
                UPDATE experiments
                SET status = 'completed', end_time = ?, winner = ?
                WHERE id = ?
            """, (datetime.now().isoformat(), winner, experiment_id))

    def health_check(self) -> Dict[str, Any]:
        """
        Perform health check.

        Returns:
            Health status information
        """
        try:
            cursor = self._conn.execute("SELECT COUNT(*) as count FROM outcomes")
            count = cursor.fetchone()['count']

            return {
                'status': 'healthy',
                'database': 'connected',
                'outcome_count': count
            }
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return {
                'status': 'unhealthy',
                'database': 'error',
                'error': str(e)
            }

    def get_stats(self) -> Dict[str, Any]:
        """
        Get database statistics.

        Returns:
            Statistics including counts
        """
        cursor = self._conn.execute("SELECT COUNT(*) as count FROM outcomes")
        outcome_count = cursor.fetchone()['count']

        cursor = self._conn.execute("SELECT COUNT(*) as count FROM experiments")
        experiment_count = cursor.fetchone()['count']

        cursor = self._conn.execute("""
            SELECT domain, COUNT(*) as count
            FROM outcomes
            GROUP BY domain
        """)
        by_domain = {row['domain']: row['count'] for row in cursor.fetchall()}

        return {
            'total_outcomes': outcome_count,
            'total_experiments': experiment_count,
            'outcomes_by_domain': by_domain
        }


if __name__ == "__main__":
    # Quick test
    tracker = OutcomeTracker()

    # Record sample outcome
    outcome = Outcome(
        domain="test",
        approach="test_approach",
        success=True,
        quality_score=0.9
    )
    outcome_id = tracker.record_outcome(outcome)
    print(f"Recorded outcome: {outcome_id}")

    # Get stats
    stats = tracker.get_stats()
    print(f"Stats: {stats}")

    # Health check
    health = tracker.health_check()
    print(f"Health: {health}")
