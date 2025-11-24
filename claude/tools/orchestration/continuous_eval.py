#!/usr/bin/env python3
"""
Continuous Evaluation System - Agentic AI Enhancement Phase 2

Implements continuous evaluation and feedback loop:
  CURRENT: Route -> Execute -> Done
  AGENTIC: Route -> Execute -> Evaluate -> Learn -> Improve Routing

Key Features:
- Auto-score agent outputs (task completion, quality metrics)
- Feed scores back to coordinator confidence weights
- Track agent performance over time
- Generate routing recommendations

Author: Maia System
Created: 2025-11-24 (Agentic AI Enhancement Project - Phase 2)
"""

import json
import sqlite3
import re
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict, field


@dataclass
class EvaluationRecord:
    """Record of an evaluation for learning"""
    task_id: str
    timestamp: datetime
    agent_used: Optional[str]
    query: str
    domain: str
    complexity: int
    output_quality: float  # 0.0-1.0 overall quality
    task_completed: bool
    user_rating: Optional[int]  # 1-5 scale if provided
    auto_score: float  # Automated scoring
    issues_found: List[str] = field(default_factory=list)


class ContinuousEvaluationSystem:
    """
    Continuous Evaluation and Feedback Loop.

    Tracks task outcomes, scores outputs automatically, and provides
    feedback to improve routing decisions over time.
    """

    # Quality thresholds
    QUALITY_THRESHOLD_LOW = 0.5
    QUALITY_THRESHOLD_HIGH = 0.8
    ALERT_THRESHOLD = 0.4

    def __init__(self, db_path: Optional[str] = None):
        """
        Initialize Continuous Evaluation System.

        Args:
            db_path: Path to SQLite database for persistence
        """
        if db_path is None:
            maia_root = Path(__file__).resolve().parents[3]
            db_path = maia_root / "claude" / "data" / "databases" / "intelligence" / "continuous_eval.db"

        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        self._init_database()

    def _init_database(self):
        """Initialize database schema"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Table 1: Evaluation Records
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS evaluations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_id TEXT UNIQUE NOT NULL,
                timestamp DATETIME NOT NULL,
                agent_used TEXT,
                query TEXT,
                domain TEXT NOT NULL,
                complexity INTEGER,
                output_quality REAL NOT NULL,
                task_completed BOOLEAN,
                user_rating INTEGER,
                auto_score REAL,
                issues_json TEXT
            )
        """)

        # Table 2: Agent Performance Aggregates
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS agent_performance (
                agent TEXT PRIMARY KEY,
                total_tasks INTEGER DEFAULT 0,
                avg_quality REAL DEFAULT 0.0,
                completion_rate REAL DEFAULT 0.0,
                avg_user_rating REAL,
                last_updated DATETIME
            )
        """)

        # Table 3: Quality Alerts
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS quality_alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME NOT NULL,
                agent TEXT,
                domain TEXT,
                alert_type TEXT NOT NULL,
                message TEXT,
                resolved BOOLEAN DEFAULT FALSE
            )
        """)

        # Indexes
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_eval_agent_time
            ON evaluations(agent_used, timestamp)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_eval_domain
            ON evaluations(domain, timestamp)
        """)

        conn.commit()
        conn.close()

    def record_evaluation(self, record: EvaluationRecord):
        """
        Record an evaluation.

        Args:
            record: EvaluationRecord with quality metrics
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute("""
                INSERT INTO evaluations
                (task_id, timestamp, agent_used, query, domain, complexity,
                 output_quality, task_completed, user_rating, auto_score, issues_json)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                record.task_id,
                record.timestamp.isoformat(),
                record.agent_used,
                record.query,
                record.domain,
                record.complexity,
                record.output_quality,
                record.task_completed,
                record.user_rating,
                record.auto_score,
                json.dumps(record.issues_found)
            ))
            conn.commit()

            # Update agent performance
            if record.agent_used:
                self._update_agent_performance(record.agent_used)

        except sqlite3.IntegrityError:
            pass  # Duplicate task_id
        finally:
            conn.close()

    def _update_agent_performance(self, agent: str):
        """Update aggregate performance for an agent"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Get recent evaluations for this agent
        cutoff = (datetime.now() - timedelta(days=30)).isoformat()

        cursor.execute("""
            SELECT
                COUNT(*) as total,
                AVG(output_quality) as avg_quality,
                AVG(CASE WHEN task_completed THEN 1.0 ELSE 0.0 END) as completion_rate,
                AVG(user_rating) as avg_rating
            FROM evaluations
            WHERE agent_used = ? AND timestamp > ?
        """, (agent, cutoff))

        row = cursor.fetchone()
        total, avg_quality, completion_rate, avg_rating = row

        cursor.execute("""
            INSERT OR REPLACE INTO agent_performance
            (agent, total_tasks, avg_quality, completion_rate, avg_user_rating, last_updated)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            agent,
            total or 0,
            avg_quality or 0.0,
            completion_rate or 0.0,
            avg_rating,
            datetime.now().isoformat()
        ))

        conn.commit()
        conn.close()

    def auto_score_output(self, output: str, query: str = None) -> float:
        """
        Automatically score an output.

        Args:
            output: The response text to score
            query: Original query (for context)

        Returns:
            Quality score (0.0-1.0)
        """
        score = 1.0
        penalties = []

        # Check for TODO/FIXME markers
        if re.search(r'\b(TODO|FIXME|XXX)\b', output, re.IGNORECASE):
            score -= 0.2
            penalties.append("incomplete_markers")

        # Check for empty or very short output
        if len(output.strip()) < 50:
            score -= 0.3
            penalties.append("too_short")

        # Check for overconfident claims
        overconfident_patterns = [
            r'100%\s+(success|guarantee|accurate)',
            r'will\s+never\s+fail',
            r'absolutely\s+(certain|guaranteed)',
            r'definitely\s+works?'
        ]
        for pattern in overconfident_patterns:
            if re.search(pattern, output, re.IGNORECASE):
                score -= 0.1
                penalties.append("overconfident")
                break

        # Check for structure (headers, lists)
        has_structure = bool(re.search(r'^#+\s|\n-\s|\n\d+\.\s', output, re.MULTILINE))
        if not has_structure and len(output) > 200:
            score -= 0.1
            penalties.append("unstructured")

        # Check for code blocks if query seems to need them
        if query:
            action_words = ['how', 'implement', 'create', 'write', 'code', 'script', 'fix']
            if any(word in query.lower() for word in action_words):
                if not re.search(r'```\w*\n', output):
                    score -= 0.15
                    penalties.append("missing_code")

        # Bonus for good practices
        if re.search(r'(note|warning|caution):', output, re.IGNORECASE):
            score += 0.05  # Has warnings/notes

        return max(0.0, min(1.0, score))

    def get_recent_evaluations(self, limit: int = 100, agent: str = None) -> List[Dict]:
        """Get recent evaluations"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        if agent:
            cursor.execute("""
                SELECT task_id, timestamp, agent_used, query, domain, complexity,
                       output_quality, task_completed, user_rating, auto_score, issues_json
                FROM evaluations
                WHERE agent_used = ?
                ORDER BY timestamp DESC
                LIMIT ?
            """, (agent, limit))
        else:
            cursor.execute("""
                SELECT task_id, timestamp, agent_used, query, domain, complexity,
                       output_quality, task_completed, user_rating, auto_score, issues_json
                FROM evaluations
                ORDER BY timestamp DESC
                LIMIT ?
            """, (limit,))

        rows = cursor.fetchall()
        conn.close()

        return [
            {
                'task_id': r[0],
                'timestamp': r[1],
                'agent_used': r[2],
                'query': r[3],
                'domain': r[4],
                'complexity': r[5],
                'output_quality': r[6],
                'task_completed': r[7],
                'user_rating': r[8],
                'auto_score': r[9],
                'issues': json.loads(r[10]) if r[10] else []
            }
            for r in rows
        ]

    def get_agent_performance(self, agent: str) -> Dict[str, Any]:
        """Get performance stats for an agent"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT total_tasks, avg_quality, completion_rate, avg_user_rating, last_updated
            FROM agent_performance
            WHERE agent = ?
        """, (agent,))

        row = cursor.fetchone()
        conn.close()

        if row:
            return {
                'agent': agent,
                'total_tasks': row[0],
                'avg_quality': row[1],
                'completion_rate': row[2],
                'avg_user_rating': row[3],
                'last_updated': row[4]
            }
        else:
            return {
                'agent': agent,
                'total_tasks': 0,
                'avg_quality': 0.0,
                'completion_rate': 0.0,
                'avg_user_rating': None,
                'last_updated': None
            }

    def get_domain_trends(self, domain: str, days: int = 30) -> Dict[str, Any]:
        """Get quality trends for a domain"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cutoff = (datetime.now() - timedelta(days=days)).isoformat()

        # Get weekly averages
        cursor.execute("""
            SELECT
                strftime('%Y-%W', timestamp) as week,
                AVG(output_quality) as avg_quality,
                COUNT(*) as count
            FROM evaluations
            WHERE domain = ? AND timestamp > ?
            GROUP BY week
            ORDER BY week
        """, (domain, cutoff))

        weeks = cursor.fetchall()

        # Calculate trend
        if len(weeks) >= 2:
            first_week = weeks[0][1] if weeks[0][1] else 0
            last_week = weeks[-1][1] if weeks[-1][1] else 0
            trend = "improving" if last_week > first_week else ("declining" if last_week < first_week else "stable")
        else:
            trend = "insufficient_data"

        # Get overall stats
        cursor.execute("""
            SELECT AVG(output_quality), COUNT(*), AVG(CASE WHEN task_completed THEN 1.0 ELSE 0.0 END)
            FROM evaluations
            WHERE domain = ? AND timestamp > ?
        """, (domain, cutoff))

        overall = cursor.fetchone()
        conn.close()

        return {
            'domain': domain,
            'trend_direction': trend,
            'avg_quality': overall[0] or 0.0,
            'total_tasks': overall[1] or 0,
            'completion_rate': overall[2] or 0.0,
            'weekly_data': [{'week': w[0], 'quality': w[1], 'count': w[2]} for w in weeks]
        }

    def get_routing_recommendations(self, domain: str) -> Dict[str, Any]:
        """
        Get recommendations for routing improvements.

        Args:
            domain: Domain to analyze

        Returns:
            Dict with recommendations
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cutoff = (datetime.now() - timedelta(days=14)).isoformat()

        # Analyze failures without agent
        cursor.execute("""
            SELECT COUNT(*), AVG(complexity)
            FROM evaluations
            WHERE domain = ? AND timestamp > ?
              AND agent_used IS NULL AND task_completed = FALSE
        """, (domain, cutoff))

        no_agent_failures = cursor.fetchone()

        # Analyze successes with agent
        cursor.execute("""
            SELECT COUNT(*), AVG(output_quality)
            FROM evaluations
            WHERE domain = ? AND timestamp > ?
              AND agent_used IS NOT NULL AND task_completed = TRUE
        """, (domain, cutoff))

        agent_successes = cursor.fetchone()

        conn.close()

        recommendations = []
        threshold_suggestion = None

        if no_agent_failures[0] and no_agent_failures[0] > 3:
            avg_complexity = no_agent_failures[1] or 3
            recommendations.append(f"Consider lowering threshold: {no_agent_failures[0]} failures without agent")
            threshold_suggestion = max(1, avg_complexity - 1)

        if agent_successes[0] and agent_successes[1] and agent_successes[1] > 0.85:
            recommendations.append("Agent performance is strong for this domain")

        return {
            'domain': domain,
            'recommendations': recommendations,
            'threshold_suggestion': threshold_suggestion,
            'no_agent_failures': no_agent_failures[0] or 0,
            'agent_success_count': agent_successes[0] or 0
        }

    def update_user_rating(self, task_id: str, rating: int):
        """Update evaluation with user rating"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE evaluations
            SET user_rating = ?
            WHERE task_id = ?
        """, (rating, task_id))

        conn.commit()

        # Get agent to update performance
        cursor.execute("SELECT agent_used FROM evaluations WHERE task_id = ?", (task_id,))
        row = cursor.fetchone()
        conn.close()

        if row and row[0]:
            self._update_agent_performance(row[0])

    def check_quality_alerts(self) -> List[Dict]:
        """Check for quality issues that need attention"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        alerts = []
        cutoff = (datetime.now() - timedelta(days=7)).isoformat()

        # Check for agents with low quality
        cursor.execute("""
            SELECT agent_used, AVG(output_quality) as avg_q, COUNT(*) as cnt
            FROM evaluations
            WHERE timestamp > ? AND agent_used IS NOT NULL
            GROUP BY agent_used
            HAVING avg_q < ? AND cnt >= 3
        """, (cutoff, self.ALERT_THRESHOLD))

        for row in cursor.fetchall():
            alerts.append({
                'type': 'low_quality_agent',
                'agent': row[0],
                'avg_quality': row[1],
                'task_count': row[2],
                'message': f"Agent {row[0]} has low quality ({row[1]:.0%}) over {row[2]} tasks"
            })

        # Check for domains with declining quality
        cursor.execute("""
            SELECT domain, AVG(output_quality) as avg_q
            FROM evaluations
            WHERE timestamp > ?
            GROUP BY domain
            HAVING avg_q < ?
        """, (cutoff, self.QUALITY_THRESHOLD_LOW))

        for row in cursor.fetchall():
            alerts.append({
                'type': 'low_quality_domain',
                'domain': row[0],
                'avg_quality': row[1],
                'message': f"Domain {row[0]} has low quality ({row[1]:.0%})"
            })

        conn.close()
        return alerts

    def export_metrics(self) -> Dict[str, Any]:
        """Export metrics for dashboard"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cutoff = (datetime.now() - timedelta(days=30)).isoformat()

        cursor.execute("""
            SELECT
                COUNT(*) as total,
                AVG(output_quality) as avg_quality,
                AVG(CASE WHEN task_completed THEN 1.0 ELSE 0.0 END) as completion_rate,
                AVG(user_rating) as avg_rating
            FROM evaluations
            WHERE timestamp > ?
        """, (cutoff,))

        overall = cursor.fetchone()

        # Per-domain breakdown
        cursor.execute("""
            SELECT domain, COUNT(*), AVG(output_quality)
            FROM evaluations
            WHERE timestamp > ?
            GROUP BY domain
        """, (cutoff,))

        domains = {r[0]: {'count': r[1], 'quality': r[2]} for r in cursor.fetchall()}

        conn.close()

        return {
            'period': '30d',
            'total_evaluations': overall[0] or 0,
            'avg_quality': overall[1] or 0.0,
            'completion_rate': overall[2] or 0.0,
            'avg_user_rating': overall[3],
            'domains': domains
        }


def main():
    """CLI for continuous evaluation system"""
    import argparse

    parser = argparse.ArgumentParser(description="Continuous Evaluation System")
    subparsers = parser.add_subparsers(dest='command', help='Commands')

    # Stats command
    stats_parser = subparsers.add_parser('stats', help='Show evaluation statistics')
    stats_parser.add_argument('--agent', '-a', help='Specific agent to show')
    stats_parser.add_argument('--domain', '-d', help='Specific domain to show')
    stats_parser.add_argument('--json', action='store_true', help='Output as JSON')

    # Alerts command
    subparsers.add_parser('alerts', help='Check quality alerts')

    # Score command
    score_parser = subparsers.add_parser('score', help='Score output text')
    score_parser.add_argument('--text', '-t', help='Text to score')
    score_parser.add_argument('--file', '-f', help='File to score')
    score_parser.add_argument('--query', '-q', help='Original query context')

    args = parser.parse_args()

    system = ContinuousEvaluationSystem()

    if args.command == 'stats':
        if args.agent:
            stats = system.get_agent_performance(args.agent)
            print(f"\nAgent: {stats['agent']}")
            print(f"  Total Tasks: {stats['total_tasks']}")
            print(f"  Avg Quality: {stats['avg_quality']:.0%}")
            print(f"  Completion Rate: {stats['completion_rate']:.0%}")
        elif args.domain:
            trends = system.get_domain_trends(args.domain)
            print(f"\nDomain: {trends['domain']}")
            print(f"  Trend: {trends['trend_direction']}")
            print(f"  Avg Quality: {trends['avg_quality']:.0%}")
            print(f"  Total Tasks: {trends['total_tasks']}")
        else:
            metrics = system.export_metrics()
            if args.json:
                print(json.dumps(metrics, indent=2))
            else:
                print(f"\n📊 Evaluation Metrics ({metrics['period']})")
                print("=" * 40)
                print(f"Total: {metrics['total_evaluations']}")
                print(f"Avg Quality: {metrics['avg_quality']:.0%}")
                print(f"Completion: {metrics['completion_rate']:.0%}")

    elif args.command == 'alerts':
        alerts = system.check_quality_alerts()
        if alerts:
            print("\n⚠️  Quality Alerts")
            print("=" * 40)
            for alert in alerts:
                print(f"  [{alert['type']}] {alert['message']}")
        else:
            print("✅ No quality alerts")

    elif args.command == 'score':
        if args.file:
            with open(args.file, 'r') as f:
                text = f.read()
        elif args.text:
            text = args.text
        else:
            print("Provide --text or --file")
            return 1

        score = system.auto_score_output(text, args.query)
        print(f"Quality Score: {score:.0%}")

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
