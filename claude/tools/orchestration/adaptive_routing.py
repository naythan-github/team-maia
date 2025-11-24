#!/usr/bin/env python3
"""
Adaptive Complexity Routing - Agentic AI Enhancement Phase 1

Implements adaptive thresholds that learn from task outcomes:
  CURRENT: complexity >= 3 -> load agent (fixed)
  AGENTIC: complexity threshold adapts based on task success rates

Key Features:
- Track success rates by complexity level and domain
- Adjust thresholds: if simple tasks failing, lower threshold
- Per-domain threshold tuning
- Persist learned thresholds to database

Author: Maia System
Created: 2025-11-24 (Agentic AI Enhancement Project - Phase 1)
"""

import json
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict, field


@dataclass
class TaskOutcome:
    """Record of a task outcome for learning"""
    task_id: str
    timestamp: datetime
    query: str
    domain: str
    complexity: int
    agent_used: Optional[str]
    agent_loaded: bool  # Was an agent loaded for this task?
    success: bool
    quality_score: float  # 0.0-1.0
    user_corrections: int  # Number of user corrections needed


@dataclass
class AdaptiveThreshold:
    """Adaptive threshold configuration for a domain"""
    domain: str
    base_threshold: int = 3  # Default complexity threshold for agent loading
    current_threshold: float = 3.0  # Adjusted threshold (can be fractional)
    success_rate: float = 0.0  # Recent success rate
    sample_count: int = 0  # Number of samples used
    last_updated: datetime = field(default_factory=datetime.now)

    def should_load_agent(self, complexity: int) -> bool:
        """Determine if agent should be loaded based on adaptive threshold"""
        return complexity >= self.current_threshold


class AdaptiveRoutingSystem:
    """
    Adaptive Complexity Routing with Learning.

    Tracks task outcomes and adjusts routing thresholds to improve:
    - When to load specialist agents
    - Per-domain threshold optimization
    - Continuous improvement based on success rates
    """

    # Learning parameters
    LEARNING_RATE = 0.1  # How fast thresholds adapt
    MIN_SAMPLES = 5  # Minimum samples before adjusting
    SUCCESS_TARGET = 0.85  # Target success rate
    THRESHOLD_MIN = 1  # Minimum complexity threshold
    THRESHOLD_MAX = 7  # Maximum complexity threshold
    DECAY_FACTOR = 0.95  # Weight decay for older samples

    def __init__(self, db_path: Optional[str] = None):
        """
        Initialize Adaptive Routing System.

        Args:
            db_path: Path to SQLite database for persistence
        """
        if db_path is None:
            maia_root = Path(__file__).resolve().parents[3]
            db_path = maia_root / "claude" / "data" / "databases" / "intelligence" / "adaptive_routing.db"

        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        self._init_database()
        self.thresholds = self._load_thresholds()

    def _init_database(self):
        """Initialize database schema"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Table 1: Task Outcomes
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS task_outcomes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_id TEXT UNIQUE NOT NULL,
                timestamp DATETIME NOT NULL,
                query TEXT,
                domain TEXT NOT NULL,
                complexity INTEGER NOT NULL,
                agent_used TEXT,
                agent_loaded BOOLEAN NOT NULL,
                success BOOLEAN NOT NULL,
                quality_score REAL,
                user_corrections INTEGER DEFAULT 0
            )
        """)

        # Table 2: Adaptive Thresholds
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS adaptive_thresholds (
                domain TEXT PRIMARY KEY,
                base_threshold INTEGER DEFAULT 3,
                current_threshold REAL DEFAULT 3.0,
                success_rate REAL DEFAULT 0.0,
                sample_count INTEGER DEFAULT 0,
                last_updated DATETIME
            )
        """)

        # Table 3: Threshold History (for analysis)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS threshold_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                domain TEXT NOT NULL,
                timestamp DATETIME NOT NULL,
                old_threshold REAL,
                new_threshold REAL,
                trigger_reason TEXT,
                sample_count INTEGER
            )
        """)

        # Index for faster queries
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_outcomes_domain_time
            ON task_outcomes(domain, timestamp)
        """)

        conn.commit()
        conn.close()

    def _load_thresholds(self) -> Dict[str, AdaptiveThreshold]:
        """Load thresholds from database"""
        thresholds = {}

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT domain, base_threshold, current_threshold,
                   success_rate, sample_count, last_updated
            FROM adaptive_thresholds
        """)

        for row in cursor.fetchall():
            domain, base, current, rate, count, updated = row
            thresholds[domain] = AdaptiveThreshold(
                domain=domain,
                base_threshold=base,
                current_threshold=current,
                success_rate=rate,
                sample_count=count,
                last_updated=datetime.fromisoformat(updated) if updated else datetime.now()
            )

        conn.close()

        # Ensure 'general' domain exists
        if 'general' not in thresholds:
            thresholds['general'] = AdaptiveThreshold(domain='general')

        return thresholds

    def _save_threshold(self, threshold: AdaptiveThreshold):
        """Save threshold to database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT OR REPLACE INTO adaptive_thresholds
            (domain, base_threshold, current_threshold, success_rate,
             sample_count, last_updated)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            threshold.domain,
            threshold.base_threshold,
            threshold.current_threshold,
            threshold.success_rate,
            threshold.sample_count,
            threshold.last_updated.isoformat()
        ))

        conn.commit()
        conn.close()

    def get_threshold(self, domain: str) -> AdaptiveThreshold:
        """Get current threshold for a domain"""
        if domain not in self.thresholds:
            # Create new threshold for unknown domain
            self.thresholds[domain] = AdaptiveThreshold(domain=domain)
            self._save_threshold(self.thresholds[domain])

        return self.thresholds[domain]

    def should_load_agent(self, domain: str, complexity: int) -> Tuple[bool, str]:
        """
        Determine if agent should be loaded based on adaptive threshold.

        Args:
            domain: Task domain (e.g., 'sre', 'security', 'general')
            complexity: Task complexity (1-10)

        Returns:
            Tuple of (should_load, reasoning)
        """
        threshold = self.get_threshold(domain)

        should_load = complexity >= threshold.current_threshold

        if should_load:
            reasoning = f"Complexity {complexity} >= threshold {threshold.current_threshold:.1f} for {domain}"
        else:
            reasoning = f"Complexity {complexity} < threshold {threshold.current_threshold:.1f} for {domain}"

        # Add context about learning
        if threshold.sample_count >= self.MIN_SAMPLES:
            reasoning += f" (learned from {threshold.sample_count} samples, {threshold.success_rate:.0%} success)"

        return should_load, reasoning

    def record_outcome(self, outcome: TaskOutcome):
        """
        Record a task outcome for learning.

        Args:
            outcome: TaskOutcome with success/failure information
        """
        # Save to database
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute("""
                INSERT INTO task_outcomes
                (task_id, timestamp, query, domain, complexity, agent_used,
                 agent_loaded, success, quality_score, user_corrections)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                outcome.task_id,
                outcome.timestamp.isoformat(),
                outcome.query,
                outcome.domain,
                outcome.complexity,
                outcome.agent_used,
                outcome.agent_loaded,
                outcome.success,
                outcome.quality_score,
                outcome.user_corrections
            ))
            conn.commit()
        except sqlite3.IntegrityError:
            # Duplicate task_id, ignore
            pass
        finally:
            conn.close()

        # Update threshold based on outcome
        self._update_threshold(outcome)

    def _update_threshold(self, outcome: TaskOutcome):
        """Update threshold based on new outcome"""
        threshold = self.get_threshold(outcome.domain)

        # Get recent outcomes for this domain
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Look at last 30 days of outcomes
        cutoff = (datetime.now() - timedelta(days=30)).isoformat()

        cursor.execute("""
            SELECT complexity, agent_loaded, success, quality_score
            FROM task_outcomes
            WHERE domain = ? AND timestamp > ?
            ORDER BY timestamp DESC
            LIMIT 100
        """, (outcome.domain, cutoff))

        outcomes = cursor.fetchall()
        conn.close()

        if len(outcomes) < self.MIN_SAMPLES:
            # Not enough data to adjust
            return

        # Calculate success rates with decay (recent samples weighted more)
        total_weight = 0
        weighted_success = 0
        agent_helped_count = 0
        agent_hurt_count = 0

        for i, (complexity, agent_loaded, success, quality) in enumerate(outcomes):
            weight = self.DECAY_FACTOR ** i

            if success:
                weighted_success += weight
            total_weight += weight

            # Track when agent loading correlates with success
            if agent_loaded and success:
                agent_helped_count += 1
            elif not agent_loaded and not success and complexity >= threshold.current_threshold - 1:
                # Failed without agent near threshold
                agent_hurt_count += 1

        if total_weight == 0:
            return

        success_rate = weighted_success / total_weight

        # Determine threshold adjustment
        old_threshold = threshold.current_threshold
        adjustment = 0

        if success_rate < self.SUCCESS_TARGET - 0.1:
            # Success rate too low - consider lowering threshold
            # (load agents earlier for more help)
            if agent_hurt_count > agent_helped_count * 0.5:
                adjustment = -self.LEARNING_RATE
        elif success_rate > self.SUCCESS_TARGET + 0.1:
            # Success rate high - can potentially raise threshold
            # (load agents less often, save resources)
            if agent_helped_count < len(outcomes) * 0.3:
                adjustment = self.LEARNING_RATE

        # Apply adjustment with bounds
        new_threshold = max(
            self.THRESHOLD_MIN,
            min(self.THRESHOLD_MAX, old_threshold + adjustment)
        )

        # Update threshold
        threshold.current_threshold = new_threshold
        threshold.success_rate = success_rate
        threshold.sample_count = len(outcomes)
        threshold.last_updated = datetime.now()

        # Save updated threshold
        self._save_threshold(threshold)
        self.thresholds[outcome.domain] = threshold

        # Log threshold change if significant
        if abs(new_threshold - old_threshold) >= 0.05:
            self._log_threshold_change(
                outcome.domain,
                old_threshold,
                new_threshold,
                f"Success rate: {success_rate:.1%}, samples: {len(outcomes)}"
            )

    def _log_threshold_change(self, domain: str, old: float, new: float, reason: str):
        """Log threshold change for analysis"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO threshold_history
            (domain, timestamp, old_threshold, new_threshold, trigger_reason, sample_count)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            domain,
            datetime.now().isoformat(),
            old,
            new,
            reason,
            self.thresholds.get(domain, AdaptiveThreshold(domain=domain)).sample_count
        ))

        conn.commit()
        conn.close()

    def get_domain_stats(self, domain: str) -> Dict[str, Any]:
        """Get statistics for a domain"""
        threshold = self.get_threshold(domain)

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Get recent outcomes
        cutoff = (datetime.now() - timedelta(days=30)).isoformat()

        cursor.execute("""
            SELECT
                COUNT(*) as total,
                SUM(CASE WHEN success THEN 1 ELSE 0 END) as successes,
                SUM(CASE WHEN agent_loaded THEN 1 ELSE 0 END) as agent_loaded,
                AVG(quality_score) as avg_quality,
                AVG(complexity) as avg_complexity
            FROM task_outcomes
            WHERE domain = ? AND timestamp > ?
        """, (domain, cutoff))

        row = cursor.fetchone()
        conn.close()

        total, successes, agent_loaded, avg_quality, avg_complexity = row

        return {
            'domain': domain,
            'current_threshold': threshold.current_threshold,
            'base_threshold': threshold.base_threshold,
            'total_tasks': total or 0,
            'success_count': successes or 0,
            'success_rate': (successes / total * 100) if total else 0,
            'agent_usage_rate': (agent_loaded / total * 100) if total else 0,
            'avg_quality': avg_quality or 0,
            'avg_complexity': avg_complexity or 0,
            'last_updated': threshold.last_updated.isoformat()
        }

    def get_all_stats(self) -> Dict[str, Any]:
        """Get statistics for all domains"""
        stats = {}
        for domain in self.thresholds:
            stats[domain] = self.get_domain_stats(domain)

        return {
            'domains': stats,
            'global': {
                'total_domains': len(self.thresholds),
                'avg_threshold': sum(t.current_threshold for t in self.thresholds.values()) / len(self.thresholds) if self.thresholds else 3.0
            }
        }

    def reset_domain(self, domain: str):
        """Reset threshold for a domain to base values"""
        threshold = AdaptiveThreshold(domain=domain)
        self.thresholds[domain] = threshold
        self._save_threshold(threshold)

        self._log_threshold_change(domain, 0, 3.0, "Manual reset")


def generate_task_id() -> str:
    """Generate unique task ID"""
    import uuid
    return str(uuid.uuid4())[:8]


def main():
    """CLI for adaptive routing system"""
    import argparse

    parser = argparse.ArgumentParser(description="Adaptive Complexity Routing System")
    subparsers = parser.add_subparsers(dest='command', help='Commands')

    # Stats command
    stats_parser = subparsers.add_parser('stats', help='Show routing statistics')
    stats_parser.add_argument('--domain', '-d', help='Specific domain to show')
    stats_parser.add_argument('--json', action='store_true', help='Output as JSON')

    # Check command
    check_parser = subparsers.add_parser('check', help='Check if agent should be loaded')
    check_parser.add_argument('domain', help='Task domain')
    check_parser.add_argument('complexity', type=int, help='Task complexity (1-10)')

    # Record command
    record_parser = subparsers.add_parser('record', help='Record a task outcome')
    record_parser.add_argument('domain', help='Task domain')
    record_parser.add_argument('complexity', type=int, help='Task complexity')
    record_parser.add_argument('--success', action='store_true', help='Task was successful')
    record_parser.add_argument('--agent', help='Agent used (if any)')
    record_parser.add_argument('--quality', type=float, default=0.8, help='Quality score 0-1')

    # Reset command
    reset_parser = subparsers.add_parser('reset', help='Reset domain threshold')
    reset_parser.add_argument('domain', help='Domain to reset')

    args = parser.parse_args()

    system = AdaptiveRoutingSystem()

    if args.command == 'stats':
        if args.domain:
            stats = system.get_domain_stats(args.domain)
        else:
            stats = system.get_all_stats()

        if args.json:
            print(json.dumps(stats, indent=2))
        else:
            print("\n📊 Adaptive Routing Statistics")
            print("=" * 50)
            if args.domain:
                print(f"\nDomain: {stats['domain']}")
                print(f"  Threshold: {stats['current_threshold']:.1f} (base: {stats['base_threshold']})")
                print(f"  Success Rate: {stats['success_rate']:.1f}%")
                print(f"  Agent Usage: {stats['agent_usage_rate']:.1f}%")
                print(f"  Tasks (30d): {stats['total_tasks']}")
            else:
                for domain, data in stats['domains'].items():
                    print(f"\n{domain}:")
                    print(f"  Threshold: {data['current_threshold']:.1f}")
                    print(f"  Success: {data['success_rate']:.1f}%")
                    print(f"  Tasks: {data['total_tasks']}")

    elif args.command == 'check':
        should_load, reasoning = system.should_load_agent(args.domain, args.complexity)
        status = "✅ LOAD AGENT" if should_load else "⏭️  SKIP AGENT"
        print(f"{status}: {reasoning}")

    elif args.command == 'record':
        outcome = TaskOutcome(
            task_id=generate_task_id(),
            timestamp=datetime.now(),
            query="CLI recorded",
            domain=args.domain,
            complexity=args.complexity,
            agent_used=args.agent,
            agent_loaded=args.agent is not None,
            success=args.success,
            quality_score=args.quality,
            user_corrections=0
        )
        system.record_outcome(outcome)
        print(f"✅ Recorded outcome for {args.domain} (complexity {args.complexity})")

    elif args.command == 'reset':
        system.reset_domain(args.domain)
        print(f"🔄 Reset threshold for {args.domain} to default (3.0)")

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
