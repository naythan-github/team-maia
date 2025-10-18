#!/usr/bin/env python3
"""
ServiceDesk Operations Intelligence Database

Purpose: Persistent operational intelligence for ServiceDesk Manager Agent
- Track insights (complaint patterns, escalation bottlenecks, skill gaps)
- Record recommendations (training, process changes, tooling)
- Log actions taken (assignments, communications, implementations)
- Measure outcomes (FCR improvement, escalation reduction, CSAT increase)
- Capture learnings (what worked, what didn't, institutional knowledge)

Author: SRE Principal Engineer Agent + ServiceDesk Manager Agent
Project: SDM-OPS-INTEL-001
Created: 2025-10-18
Phase: 127+ (SDM Project Extension)
"""

import os
import sys
import sqlite3
import json
import argparse
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass, asdict
import textwrap

# Path setup
MAIA_ROOT = Path(os.environ.get('MAIA_ROOT', Path.home() / 'git' / 'maia'))
DB_PATH = MAIA_ROOT / 'claude' / 'data' / 'servicedesk_operations_intelligence.db'


@dataclass
class OperationalInsight:
    """Identified problem or pattern from analysis"""
    insight_id: Optional[int] = None
    insight_type: str = ''  # complaint_pattern, escalation_bottleneck, fcr_opportunity, skill_gap, client_at_risk
    title: str = ''
    description: str = ''
    identified_date: str = ''
    severity: str = ''  # critical, high, medium, low
    affected_clients: str = ''  # JSON array
    affected_categories: str = ''  # JSON array
    affected_ticket_ids: str = ''  # JSON array
    root_cause: str = ''
    business_impact: str = ''
    status: str = 'active'  # active, resolved, monitoring, archived
    created_at: str = ''
    updated_at: str = ''


@dataclass
class Recommendation:
    """Recommended intervention with effort/impact estimates"""
    recommendation_id: Optional[int] = None
    insight_id: int = 0
    recommendation_type: str = ''  # training, process_change, staffing, tooling, knowledge_base, skill_routing, customer_communication
    title: str = ''
    description: str = ''
    estimated_effort: str = ''
    estimated_impact: str = ''
    priority: str = ''  # critical, high, medium, low
    status: str = 'proposed'  # proposed, approved, in_progress, completed, abandoned
    assigned_to: str = ''
    due_date: str = ''
    created_at: str = ''
    updated_at: str = ''


@dataclass
class ActionTaken:
    """Actual intervention performed"""
    action_id: Optional[int] = None
    recommendation_id: int = 0
    action_type: str = ''  # ticket_assignment, customer_communication, training_session, kb_article, process_update, tool_implementation
    action_date: str = ''
    performed_by: str = ''
    details: str = ''
    ticket_ids: str = ''  # JSON array
    artifacts: str = ''  # JSON object
    created_at: str = ''


@dataclass
class Outcome:
    """Measured impact of recommendation"""
    outcome_id: Optional[int] = None
    recommendation_id: int = 0
    measurement_date: str = ''
    metric_type: str = ''  # fcr_rate, escalation_rate, csat_score, resolution_time_avg, sla_compliance, client_complaints
    baseline_value: float = 0.0
    current_value: float = 0.0
    improvement_pct: float = 0.0
    target_value: float = 0.0
    measurement_period: str = ''
    sample_size: int = 0
    notes: str = ''
    created_at: str = ''


@dataclass
class Pattern:
    """Recurring operational pattern"""
    pattern_id: Optional[int] = None
    pattern_type: str = ''  # recurring_complaint, escalation_hotspot, client_at_risk, seasonal_spike, technician_bottleneck
    pattern_description: str = ''
    first_observed: str = ''
    last_observed: str = ''
    frequency: str = ''
    occurrence_count: int = 1
    related_insights: str = ''  # JSON array
    related_tickets: str = ''  # JSON array
    trigger_conditions: str = ''
    status: str = 'active'
    created_at: str = ''
    updated_at: str = ''


@dataclass
class Learning:
    """Institutional knowledge from outcomes"""
    learning_id: Optional[int] = None
    insight_id: Optional[int] = None
    recommendation_id: Optional[int] = None
    learning_type: str = ''  # success, partial_success, failure, unexpected_outcome
    what_worked: str = ''
    what_didnt_work: str = ''
    why_analysis: str = ''
    confidence_before: float = 0.0
    confidence_after: float = 0.0
    would_recommend_again: bool = True
    similar_situations: str = ''
    tags: str = ''  # JSON array
    created_at: str = ''


class ServiceDeskOpsIntelligence:
    """ServiceDesk Operations Intelligence Database Manager"""

    def __init__(self, db_path: Path = DB_PATH):
        """Initialize database connection"""
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_database()

    def _init_database(self):
        """Create database schema with all 6 tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Table 1: Operational Insights
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS operational_insights (
                insight_id INTEGER PRIMARY KEY AUTOINCREMENT,
                insight_type TEXT NOT NULL,
                title TEXT NOT NULL,
                description TEXT,
                identified_date TEXT NOT NULL,
                severity TEXT,
                affected_clients TEXT,
                affected_categories TEXT,
                affected_ticket_ids TEXT,
                root_cause TEXT,
                business_impact TEXT,
                status TEXT DEFAULT 'active',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Table 2: Recommendations
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS recommendations (
                recommendation_id INTEGER PRIMARY KEY AUTOINCREMENT,
                insight_id INTEGER NOT NULL,
                recommendation_type TEXT NOT NULL,
                title TEXT NOT NULL,
                description TEXT,
                estimated_effort TEXT,
                estimated_impact TEXT,
                priority TEXT,
                status TEXT DEFAULT 'proposed',
                assigned_to TEXT,
                due_date TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (insight_id) REFERENCES operational_insights(insight_id)
            )
        ''')

        # Table 3: Actions Taken
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS actions_taken (
                action_id INTEGER PRIMARY KEY AUTOINCREMENT,
                recommendation_id INTEGER NOT NULL,
                action_type TEXT NOT NULL,
                action_date TEXT NOT NULL,
                performed_by TEXT,
                details TEXT,
                ticket_ids TEXT,
                artifacts TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (recommendation_id) REFERENCES recommendations(recommendation_id)
            )
        ''')

        # Table 4: Outcomes
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS outcomes (
                outcome_id INTEGER PRIMARY KEY AUTOINCREMENT,
                recommendation_id INTEGER NOT NULL,
                measurement_date TEXT NOT NULL,
                metric_type TEXT NOT NULL,
                baseline_value REAL,
                current_value REAL,
                improvement_pct REAL,
                target_value REAL,
                measurement_period TEXT,
                sample_size INTEGER,
                notes TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (recommendation_id) REFERENCES recommendations(recommendation_id)
            )
        ''')

        # Table 5: Patterns
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS patterns (
                pattern_id INTEGER PRIMARY KEY AUTOINCREMENT,
                pattern_type TEXT NOT NULL,
                pattern_description TEXT NOT NULL,
                first_observed TEXT NOT NULL,
                last_observed TEXT NOT NULL,
                frequency TEXT,
                occurrence_count INTEGER DEFAULT 1,
                related_insights TEXT,
                related_tickets TEXT,
                trigger_conditions TEXT,
                status TEXT DEFAULT 'active',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Table 6: Learning Log
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS learning_log (
                learning_id INTEGER PRIMARY KEY AUTOINCREMENT,
                insight_id INTEGER,
                recommendation_id INTEGER,
                learning_type TEXT,
                what_worked TEXT,
                what_didnt_work TEXT,
                why_analysis TEXT,
                confidence_before REAL,
                confidence_after REAL,
                would_recommend_again BOOLEAN,
                similar_situations TEXT,
                tags TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (insight_id) REFERENCES operational_insights(insight_id),
                FOREIGN KEY (recommendation_id) REFERENCES recommendations(recommendation_id)
            )
        ''')

        # Create indexes for performance
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_insights_type ON operational_insights(insight_type)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_insights_status ON operational_insights(status)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_insights_date ON operational_insights(identified_date)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_recommendations_insight ON recommendations(insight_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_recommendations_status ON recommendations(status)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_recommendations_priority ON recommendations(priority)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_actions_recommendation ON actions_taken(recommendation_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_actions_date ON actions_taken(action_date)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_outcomes_recommendation ON outcomes(recommendation_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_outcomes_metric ON outcomes(metric_type)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_outcomes_date ON outcomes(measurement_date)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_patterns_type ON patterns(pattern_type)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_patterns_status ON patterns(status)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_learning_type ON learning_log(learning_type)')

        conn.commit()
        conn.close()

    # ===== CRUD Operations: Insights =====

    def add_insight(self, insight: OperationalInsight) -> int:
        """Add new operational insight"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            INSERT INTO operational_insights (
                insight_type, title, description, identified_date, severity,
                affected_clients, affected_categories, affected_ticket_ids,
                root_cause, business_impact, status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            insight.insight_type, insight.title, insight.description,
            insight.identified_date, insight.severity, insight.affected_clients,
            insight.affected_categories, insight.affected_ticket_ids,
            insight.root_cause, insight.business_impact, insight.status
        ))

        insight_id = cursor.lastrowid
        conn.commit()
        conn.close()

        print(f"✅ Insight added: ID={insight_id}, Type={insight.insight_type}, Title={insight.title}")
        return insight_id

    def get_insights(self, status: str = None, insight_type: str = None, limit: int = 100) -> List[Dict]:
        """Get insights with optional filtering"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        query = 'SELECT * FROM operational_insights WHERE 1=1'
        params = []

        if status:
            query += ' AND status = ?'
            params.append(status)

        if insight_type:
            query += ' AND insight_type = ?'
            params.append(insight_type)

        query += ' ORDER BY identified_date DESC LIMIT ?'
        params.append(limit)

        cursor.execute(query, params)
        results = [dict(row) for row in cursor.fetchall()]
        conn.close()

        return results

    # ===== CRUD Operations: Recommendations =====

    def add_recommendation(self, rec: Recommendation) -> int:
        """Add new recommendation"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            INSERT INTO recommendations (
                insight_id, recommendation_type, title, description,
                estimated_effort, estimated_impact, priority, status,
                assigned_to, due_date
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            rec.insight_id, rec.recommendation_type, rec.title, rec.description,
            rec.estimated_effort, rec.estimated_impact, rec.priority, rec.status,
            rec.assigned_to, rec.due_date
        ))

        rec_id = cursor.lastrowid
        conn.commit()
        conn.close()

        print(f"✅ Recommendation added: ID={rec_id}, Type={rec.recommendation_type}, Priority={rec.priority}")
        return rec_id

    def get_recommendations(self, insight_id: int = None, status: str = None, priority: str = None, limit: int = 100) -> List[Dict]:
        """Get recommendations with optional filtering"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        query = 'SELECT * FROM recommendations WHERE 1=1'
        params = []

        if insight_id:
            query += ' AND insight_id = ?'
            params.append(insight_id)

        if status:
            query += ' AND status = ?'
            params.append(status)

        if priority:
            query += ' AND priority = ?'
            params.append(priority)

        query += ' ORDER BY created_at DESC LIMIT ?'
        params.append(limit)

        cursor.execute(query, params)
        results = [dict(row) for row in cursor.fetchall()]
        conn.close()

        return results

    # ===== CRUD Operations: Actions =====

    def log_action(self, action: ActionTaken) -> int:
        """Log action taken"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            INSERT INTO actions_taken (
                recommendation_id, action_type, action_date, performed_by,
                details, ticket_ids, artifacts
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            action.recommendation_id, action.action_type, action.action_date,
            action.performed_by, action.details, action.ticket_ids, action.artifacts
        ))

        action_id = cursor.lastrowid
        conn.commit()
        conn.close()

        print(f"✅ Action logged: ID={action_id}, Type={action.action_type}, Date={action.action_date}")
        return action_id

    def get_actions(self, recommendation_id: int = None, limit: int = 100) -> List[Dict]:
        """Get actions with optional filtering"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        query = 'SELECT * FROM actions_taken WHERE 1=1'
        params = []

        if recommendation_id:
            query += ' AND recommendation_id = ?'
            params.append(recommendation_id)

        query += ' ORDER BY action_date DESC LIMIT ?'
        params.append(limit)

        cursor.execute(query, params)
        results = [dict(row) for row in cursor.fetchall()]
        conn.close()

        return results

    # ===== CRUD Operations: Outcomes =====

    def track_outcome(self, outcome: Outcome) -> int:
        """Track outcome measurement"""
        # Calculate improvement percentage
        if outcome.baseline_value > 0:
            outcome.improvement_pct = ((outcome.current_value - outcome.baseline_value) / outcome.baseline_value) * 100

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            INSERT INTO outcomes (
                recommendation_id, measurement_date, metric_type, baseline_value,
                current_value, improvement_pct, target_value, measurement_period,
                sample_size, notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            outcome.recommendation_id, outcome.measurement_date, outcome.metric_type,
            outcome.baseline_value, outcome.current_value, outcome.improvement_pct,
            outcome.target_value, outcome.measurement_period, outcome.sample_size,
            outcome.notes
        ))

        outcome_id = cursor.lastrowid
        conn.commit()
        conn.close()

        print(f"✅ Outcome tracked: ID={outcome_id}, Metric={outcome.metric_type}, Improvement={outcome.improvement_pct:.1f}%")
        return outcome_id

    def get_outcomes(self, recommendation_id: int = None, metric_type: str = None, limit: int = 100) -> List[Dict]:
        """Get outcomes with optional filtering"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        query = 'SELECT * FROM outcomes WHERE 1=1'
        params = []

        if recommendation_id:
            query += ' AND recommendation_id = ?'
            params.append(recommendation_id)

        if metric_type:
            query += ' AND metric_type = ?'
            params.append(metric_type)

        query += ' ORDER BY measurement_date DESC LIMIT ?'
        params.append(limit)

        cursor.execute(query, params)
        results = [dict(row) for row in cursor.fetchall()]
        conn.close()

        return results

    # ===== CRUD Operations: Patterns =====

    def add_pattern(self, pattern: Pattern) -> int:
        """Add recurring pattern"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            INSERT INTO patterns (
                pattern_type, pattern_description, first_observed, last_observed,
                frequency, occurrence_count, related_insights, related_tickets,
                trigger_conditions, status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            pattern.pattern_type, pattern.pattern_description, pattern.first_observed,
            pattern.last_observed, pattern.frequency, pattern.occurrence_count,
            pattern.related_insights, pattern.related_tickets, pattern.trigger_conditions,
            pattern.status
        ))

        pattern_id = cursor.lastrowid
        conn.commit()
        conn.close()

        print(f"✅ Pattern added: ID={pattern_id}, Type={pattern.pattern_type}")
        return pattern_id

    def get_patterns(self, status: str = None, pattern_type: str = None, limit: int = 100) -> List[Dict]:
        """Get patterns with optional filtering"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        query = 'SELECT * FROM patterns WHERE 1=1'
        params = []

        if status:
            query += ' AND status = ?'
            params.append(status)

        if pattern_type:
            query += ' AND pattern_type = ?'
            params.append(pattern_type)

        query += ' ORDER BY last_observed DESC LIMIT ?'
        params.append(limit)

        cursor.execute(query, params)
        results = [dict(row) for row in cursor.fetchall()]
        conn.close()

        return results

    # ===== CRUD Operations: Learning Log =====

    def add_learning(self, learning: Learning) -> int:
        """Add learning entry"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            INSERT INTO learning_log (
                insight_id, recommendation_id, learning_type, what_worked,
                what_didnt_work, why_analysis, confidence_before, confidence_after,
                would_recommend_again, similar_situations, tags
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            learning.insight_id, learning.recommendation_id, learning.learning_type,
            learning.what_worked, learning.what_didnt_work, learning.why_analysis,
            learning.confidence_before, learning.confidence_after,
            learning.would_recommend_again, learning.similar_situations, learning.tags
        ))

        learning_id = cursor.lastrowid
        conn.commit()
        conn.close()

        print(f"✅ Learning logged: ID={learning_id}, Type={learning.learning_type}, Confidence: {learning.confidence_before}→{learning.confidence_after}")
        return learning_id

    def get_learning(self, learning_type: str = None, tags: str = None, limit: int = 100) -> List[Dict]:
        """Get learning entries with optional filtering"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        query = 'SELECT * FROM learning_log WHERE 1=1'
        params = []

        if learning_type:
            query += ' AND learning_type = ?'
            params.append(learning_type)

        if tags:
            query += ' AND tags LIKE ?'
            params.append(f'%{tags}%')

        query += ' ORDER BY created_at DESC LIMIT ?'
        params.append(limit)

        cursor.execute(query, params)
        results = [dict(row) for row in cursor.fetchall()]
        conn.close()

        return results

    # ===== Search & Query Functions =====

    def search(self, keyword: str, limit: int = 50) -> Dict[str, List[Dict]]:
        """Search across all tables for keyword"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row

        results = {
            'insights': [],
            'recommendations': [],
            'patterns': [],
            'learning': []
        }

        # Search insights
        cursor = conn.cursor()
        cursor.execute('''
            SELECT * FROM operational_insights
            WHERE title LIKE ? OR description LIKE ? OR root_cause LIKE ?
            ORDER BY identified_date DESC
            LIMIT ?
        ''', (f'%{keyword}%', f'%{keyword}%', f'%{keyword}%', limit))
        results['insights'] = [dict(row) for row in cursor.fetchall()]

        # Search recommendations
        cursor.execute('''
            SELECT * FROM recommendations
            WHERE title LIKE ? OR description LIKE ?
            ORDER BY created_at DESC
            LIMIT ?
        ''', (f'%{keyword}%', f'%{keyword}%', limit))
        results['recommendations'] = [dict(row) for row in cursor.fetchall()]

        # Search patterns
        cursor.execute('''
            SELECT * FROM patterns
            WHERE pattern_description LIKE ?
            ORDER BY last_observed DESC
            LIMIT ?
        ''', (f'%{keyword}%', limit))
        results['patterns'] = [dict(row) for row in cursor.fetchall()]

        # Search learning
        cursor.execute('''
            SELECT * FROM learning_log
            WHERE what_worked LIKE ? OR what_didnt_work LIKE ? OR why_analysis LIKE ?
            ORDER BY created_at DESC
            LIMIT ?
        ''', (f'%{keyword}%', f'%{keyword}%', f'%{keyword}%', limit))
        results['learning'] = [dict(row) for row in cursor.fetchall()]

        conn.close()
        return results

    def get_dashboard_summary(self) -> Dict:
        """Get summary statistics for dashboard"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        summary = {}

        # Insights summary
        cursor.execute('SELECT COUNT(*) FROM operational_insights WHERE status = "active"')
        summary['active_insights'] = cursor.fetchone()[0]

        cursor.execute('SELECT COUNT(*) FROM operational_insights WHERE severity = "critical"')
        summary['critical_insights'] = cursor.fetchone()[0]

        # Recommendations summary
        cursor.execute('SELECT COUNT(*) FROM recommendations WHERE status = "in_progress"')
        summary['in_progress_recommendations'] = cursor.fetchone()[0]

        cursor.execute('SELECT COUNT(*) FROM recommendations WHERE status = "completed"')
        summary['completed_recommendations'] = cursor.fetchone()[0]

        # Outcomes summary
        cursor.execute('SELECT AVG(improvement_pct) FROM outcomes')
        avg_improvement = cursor.fetchone()[0]
        summary['avg_improvement_pct'] = round(avg_improvement, 1) if avg_improvement else 0.0

        cursor.execute('SELECT COUNT(*) FROM outcomes WHERE improvement_pct > 0')
        summary['positive_outcomes'] = cursor.fetchone()[0]

        # Learning summary
        cursor.execute('SELECT COUNT(*) FROM learning_log WHERE learning_type = "success"')
        summary['successful_learnings'] = cursor.fetchone()[0]

        cursor.execute('SELECT AVG(confidence_after - confidence_before) FROM learning_log')
        avg_confidence_gain = cursor.fetchone()[0]
        summary['avg_confidence_gain'] = round(avg_confidence_gain, 1) if avg_confidence_gain else 0.0

        conn.close()
        return summary


def main():
    """CLI interface"""
    parser = argparse.ArgumentParser(description='ServiceDesk Operations Intelligence Database')
    subparsers = parser.add_subparsers(dest='command', help='Commands')

    # Dashboard command
    parser_dashboard = subparsers.add_parser('dashboard', help='Show dashboard summary')

    # Search command
    parser_search = subparsers.add_parser('search', help='Search across all tables')
    parser_search.add_argument('keyword', help='Search keyword')

    # Show commands
    parser_show_insights = subparsers.add_parser('show-insights', help='Show insights')
    parser_show_insights.add_argument('--status', help='Filter by status')
    parser_show_insights.add_argument('--type', help='Filter by insight type')

    parser_show_recs = subparsers.add_parser('show-recommendations', help='Show recommendations')
    parser_show_recs.add_argument('--status', help='Filter by status')
    parser_show_recs.add_argument('--priority', help='Filter by priority')

    parser_show_outcomes = subparsers.add_parser('show-outcomes', help='Show outcomes')
    parser_show_outcomes.add_argument('--metric', help='Filter by metric type')

    parser_show_learning = subparsers.add_parser('show-learning', help='Show learning entries')
    parser_show_learning.add_argument('--type', help='Filter by learning type')
    parser_show_learning.add_argument('--tags', help='Filter by tags')

    args = parser.parse_args()

    # Initialize database
    ops_intel = ServiceDeskOpsIntelligence()

    if args.command == 'dashboard':
        summary = ops_intel.get_dashboard_summary()
        print("\n" + "="*80)
        print("SERVICEDESK OPERATIONS INTELLIGENCE DASHBOARD")
        print("="*80)
        print(f"\n📊 INSIGHTS:")
        print(f"   Active Insights: {summary['active_insights']}")
        print(f"   Critical Insights: {summary['critical_insights']}")
        print(f"\n💡 RECOMMENDATIONS:")
        print(f"   In Progress: {summary['in_progress_recommendations']}")
        print(f"   Completed: {summary['completed_recommendations']}")
        print(f"\n📈 OUTCOMES:")
        print(f"   Average Improvement: {summary['avg_improvement_pct']}%")
        print(f"   Positive Outcomes: {summary['positive_outcomes']}")
        print(f"\n🎓 LEARNING:")
        print(f"   Successful Learnings: {summary['successful_learnings']}")
        print(f"   Avg Confidence Gain: {summary['avg_confidence_gain']} points")
        print("="*80 + "\n")

    elif args.command == 'search':
        results = ops_intel.search(args.keyword)
        print(f"\n🔍 Search results for '{args.keyword}':\n")
        print(f"Insights: {len(results['insights'])} found")
        print(f"Recommendations: {len(results['recommendations'])} found")
        print(f"Patterns: {len(results['patterns'])} found")
        print(f"Learning: {len(results['learning'])} found\n")

        for insight in results['insights'][:5]:
            print(f"  📌 [{insight['insight_type']}] {insight['title']}")

    elif args.command == 'show-insights':
        insights = ops_intel.get_insights(status=args.status, insight_type=args.type)
        print(f"\n📊 Insights ({len(insights)} found):\n")
        for insight in insights:
            print(f"  ID: {insight['insight_id']}")
            print(f"  Type: {insight['insight_type']} | Severity: {insight['severity']} | Status: {insight['status']}")
            print(f"  Title: {insight['title']}")
            print(f"  Date: {insight['identified_date']}")
            print(f"  Root Cause: {insight['root_cause'][:100]}...")
            print()

    elif args.command == 'show-recommendations':
        recs = ops_intel.get_recommendations(status=args.status, priority=args.priority)
        print(f"\n💡 Recommendations ({len(recs)} found):\n")
        for rec in recs:
            print(f"  ID: {rec['recommendation_id']} | Insight: {rec['insight_id']}")
            print(f"  Type: {rec['recommendation_type']} | Priority: {rec['priority']} | Status: {rec['status']}")
            print(f"  Title: {rec['title']}")
            print(f"  Impact: {rec['estimated_impact']}")
            print()

    elif args.command == 'show-outcomes':
        outcomes = ops_intel.get_outcomes(metric_type=args.metric)
        print(f"\n📈 Outcomes ({len(outcomes)} found):\n")
        for outcome in outcomes:
            print(f"  ID: {outcome['outcome_id']} | Rec: {outcome['recommendation_id']}")
            print(f"  Metric: {outcome['metric_type']}")
            print(f"  Baseline: {outcome['baseline_value']} → Current: {outcome['current_value']} (Improvement: {outcome['improvement_pct']:.1f}%)")
            print(f"  Period: {outcome['measurement_period']} | Sample: {outcome['sample_size']}")
            print()

    elif args.command == 'show-learning':
        learning = ops_intel.get_learning(learning_type=args.type, tags=args.tags)
        print(f"\n🎓 Learning Entries ({len(learning)} found):\n")
        for entry in learning:
            print(f"  ID: {entry['learning_id']} | Type: {entry['learning_type']}")
            print(f"  What Worked: {entry['what_worked'][:100]}...")
            print(f"  Confidence: {entry['confidence_before']} → {entry['confidence_after']}")
            print(f"  Would Recommend Again: {entry['would_recommend_again']}")
            print()

    else:
        parser.print_help()


if __name__ == '__main__':
    main()
