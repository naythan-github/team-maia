#!/usr/bin/env python3
"""
Decision Intelligence Agent - Phase 2 Session 3

Systematic decision capture with outcome tracking, quality scoring,
and pattern recognition for continuous learning.

Author: Maia (My AI Agent)
Created: 2025-10-13
Phase: 115 (Information Management System - Phase 2)
"""

import os
import sys
import sqlite3
import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional

# Path setup
MAIA_ROOT = Path(os.environ.get('MAIA_ROOT', Path.home() / 'git' / 'maia' / 'claude'))


class DecisionIntelligenceAgent:
    """
    Systematic decision capture with outcome tracking and learning.

    Implements 8 decision templates with quality scoring framework
    for continuous decision-making improvement.
    """

    DECISION_TEMPLATES = {
        'strategic': {
            'name': 'Strategic Decision',
            'description': 'High-impact decisions affecting long-term direction',
            'typical_timeframe': '3-6 months',
            'required_sections': ['strategic_context', 'alternatives', 'risk_assessment', 'success_metrics']
        },
        'hire': {
            'name': 'Hiring Decision',
            'description': 'Team member selection and role design',
            'typical_timeframe': '1-3 months',
            'required_sections': ['role_requirements', 'candidate_evaluation', 'team_fit', 'growth_potential']
        },
        'vendor': {
            'name': 'Vendor Selection',
            'description': 'Third-party service or tool evaluation',
            'typical_timeframe': '1-2 months',
            'required_sections': ['requirements', 'vendor_comparison', 'cost_analysis', 'integration_plan']
        },
        'architecture': {
            'name': 'Technical Architecture',
            'description': 'System design and technology choices',
            'typical_timeframe': '2-4 months',
            'required_sections': ['technical_requirements', 'architecture_options', 'trade_offs', 'scalability']
        },
        'resource': {
            'name': 'Resource Allocation',
            'description': 'Budget, time, or people allocation',
            'typical_timeframe': '1 month',
            'required_sections': ['resource_request', 'business_case', 'alternatives', 'roi_estimate']
        },
        'process': {
            'name': 'Process Change',
            'description': 'Workflow or procedure modifications',
            'typical_timeframe': '2-4 weeks',
            'required_sections': ['current_state', 'proposed_change', 'impact_assessment', 'rollout_plan']
        },
        'incident': {
            'name': 'Incident Response',
            'description': 'Critical issue resolution decisions',
            'typical_timeframe': 'Hours to days',
            'required_sections': ['incident_summary', 'response_options', 'trade_offs', 'communication_plan']
        },
        'investment': {
            'name': 'Investment Decision',
            'description': 'Significant financial or time investment',
            'typical_timeframe': '1-3 months',
            'required_sections': ['investment_proposal', 'expected_return', 'risks', 'alternatives']
        }
    }

    def __init__(self, db_path: Optional[Path] = None):
        """Initialize agent with database"""
        self.db_path = db_path or MAIA_ROOT / "data" / "databases" / "decision_intelligence.db"
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        self._init_database()

    def _init_database(self):
        """Create database schema"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Table 1: Decisions
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS decisions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                decision_type TEXT NOT NULL,
                title TEXT NOT NULL,
                problem_statement TEXT,
                context TEXT,
                decision_date TEXT NOT NULL,
                decided_by TEXT,
                stakeholders TEXT,
                status TEXT DEFAULT 'pending',
                reviewed_at TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Table 2: Decision Options
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS decision_options (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                decision_id INTEGER NOT NULL,
                option_name TEXT NOT NULL,
                description TEXT,
                pros TEXT,
                cons TEXT,
                risks TEXT,
                estimated_effort TEXT,
                estimated_cost TEXT,
                is_chosen BOOLEAN DEFAULT 0,
                FOREIGN KEY (decision_id) REFERENCES decisions(id)
            )
        ''')

        # Table 3: Decision Outcomes
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS decision_outcomes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                decision_id INTEGER NOT NULL,
                expected_outcome TEXT,
                actual_outcome TEXT,
                outcome_date TEXT,
                success_level TEXT,
                lessons_learned TEXT,
                would_decide_again BOOLEAN,
                confidence_was REAL,
                confidence_now REAL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (decision_id) REFERENCES decisions(id)
            )
        ''')

        # Table 4: Decision Quality Scores
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS decision_quality (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                decision_id INTEGER NOT NULL,
                frame_score REAL,
                alternatives_score REAL,
                information_score REAL,
                values_score REAL,
                reasoning_score REAL,
                commitment_score REAL,
                total_score REAL,
                evaluated_at TEXT NOT NULL,
                notes TEXT,
                FOREIGN KEY (decision_id) REFERENCES decisions(id)
            )
        ''')

        conn.commit()
        conn.close()

        print(f"✅ Database initialized: {self.db_path}")

    def create_decision(self, decision_type: str, title: str,
                       problem_statement: str, context: Optional[str] = None,
                       decided_by: Optional[str] = None,
                       stakeholders: Optional[List[str]] = None) -> int:
        """
        Create new decision record.

        Args:
            decision_type: Type from DECISION_TEMPLATES
            title: Decision title
            problem_statement: What problem are we solving?
            context: Background information
            decided_by: Decision maker name
            stakeholders: List of stakeholder names/emails

        Returns:
            Decision ID
        """
        if decision_type not in self.DECISION_TEMPLATES:
            print(f"⚠️  Unknown decision type: {decision_type}")
            print(f"   Valid types: {', '.join(self.DECISION_TEMPLATES.keys())}")
            decision_type = 'strategic'

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        stakeholders_str = json.dumps(stakeholders) if stakeholders else None

        cursor.execute('''
            INSERT INTO decisions (
                decision_type, title, problem_statement, context,
                decision_date, decided_by, stakeholders
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            decision_type,
            title,
            problem_statement,
            context,
            datetime.now().isoformat(),
            decided_by,
            stakeholders_str
        ))

        decision_id = cursor.lastrowid
        conn.commit()
        conn.close()

        print(f"✅ Decision created: {title} (ID: {decision_id}, Type: {decision_type})")
        return decision_id

    def add_option(self, decision_id: int, option_name: str,
                   description: Optional[str] = None,
                   pros: Optional[List[str]] = None,
                   cons: Optional[List[str]] = None,
                   risks: Optional[List[str]] = None,
                   estimated_effort: Optional[str] = None,
                   estimated_cost: Optional[str] = None) -> int:
        """
        Add option to decision.

        Returns:
            Option ID
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            INSERT INTO decision_options (
                decision_id, option_name, description, pros, cons, risks,
                estimated_effort, estimated_cost
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            decision_id,
            option_name,
            description,
            json.dumps(pros) if pros else None,
            json.dumps(cons) if cons else None,
            json.dumps(risks) if risks else None,
            estimated_effort,
            estimated_cost
        ))

        option_id = cursor.lastrowid
        conn.commit()
        conn.close()

        print(f"✅ Option added: {option_name} (ID: {option_id})")
        return option_id

    def choose_option(self, decision_id: int, option_id: int,
                     reasoning: Optional[str] = None) -> bool:
        """
        Mark option as chosen.

        Args:
            decision_id: Decision ID
            option_id: Option to choose
            reasoning: Why this option was chosen

        Returns:
            Success boolean
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Unmark all options for this decision
        cursor.execute('''
            UPDATE decision_options
            SET is_chosen = 0
            WHERE decision_id = ?
        ''', (decision_id,))

        # Mark chosen option
        cursor.execute('''
            UPDATE decision_options
            SET is_chosen = 1
            WHERE id = ? AND decision_id = ?
        ''', (option_id, decision_id))

        # Update decision status
        cursor.execute('''
            UPDATE decisions
            SET status = 'decided', updated_at = ?
            WHERE id = ?
        ''', (datetime.now().isoformat(), decision_id))

        # Store reasoning in context if provided
        if reasoning:
            cursor.execute('''
                UPDATE decisions
                SET context = context || ? || ?
                WHERE id = ?
            ''', ('\n\n**Decision Reasoning:**\n', reasoning, decision_id))

        conn.commit()
        conn.close()

        print(f"✅ Option {option_id} chosen for decision {decision_id}")
        return True

    def record_outcome(self, decision_id: int, actual_outcome: str,
                      success_level: str, lessons_learned: Optional[str] = None,
                      would_decide_again: Optional[bool] = None) -> int:
        """
        Record decision outcome after implementation.

        Args:
            decision_id: Decision ID
            actual_outcome: What actually happened
            success_level: exceeded, met, partial, missed, failed
            lessons_learned: What did we learn?
            would_decide_again: Would we make same decision?

        Returns:
            Outcome ID
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Get expected outcome
        cursor.execute('SELECT context FROM decisions WHERE id = ?', (decision_id,))
        result = cursor.fetchone()
        expected_outcome = result[0] if result else None

        cursor.execute('''
            INSERT INTO decision_outcomes (
                decision_id, expected_outcome, actual_outcome, outcome_date,
                success_level, lessons_learned, would_decide_again
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            decision_id,
            expected_outcome,
            actual_outcome,
            datetime.now().isoformat(),
            success_level,
            lessons_learned,
            would_decide_again
        ))

        outcome_id = cursor.lastrowid

        # Update decision status
        cursor.execute('''
            UPDATE decisions
            SET status = 'completed', reviewed_at = ?
            WHERE id = ?
        ''', (datetime.now().isoformat(), decision_id))

        conn.commit()
        conn.close()

        print(f"✅ Outcome recorded for decision {decision_id} (success: {success_level})")
        return outcome_id

    def calculate_quality_score(self, decision_id: int) -> Dict:
        """
        Calculate decision quality score using 6-dimension framework.

        Quality Framework (60 points total):
            1. Frame (10 pts): Clear problem statement, context, stakeholders
            2. Alternatives (10 pts): Multiple options with pros/cons/risks
            3. Information (10 pts): Sufficient data, research, consultation
            4. Values (10 pts): Alignment with strategic priorities
            5. Reasoning (10 pts): Clear logic, trade-off analysis
            6. Commitment (10 pts): Clear action plan, ownership, follow-through

        Returns:
            Score breakdown dict
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Get decision
        cursor.execute('SELECT * FROM decisions WHERE id = ?', (decision_id,))
        decision = cursor.fetchone()
        if not decision:
            conn.close()
            return {}

        scores = {}

        # 1. Frame Score (0-10)
        frame_score = 0
        if decision[2]:  # problem_statement
            frame_score += 4
        if decision[3]:  # context
            frame_score += 3
        if decision[6]:  # stakeholders
            frame_score += 3
        scores['frame'] = min(10, frame_score)

        # 2. Alternatives Score (0-10)
        cursor.execute('SELECT COUNT(*) FROM decision_options WHERE decision_id = ?', (decision_id,))
        option_count = cursor.fetchone()[0]

        cursor.execute('''
            SELECT COUNT(*) FROM decision_options
            WHERE decision_id = ? AND pros IS NOT NULL AND cons IS NOT NULL AND risks IS NOT NULL
        ''', (decision_id,))
        complete_options = cursor.fetchone()[0]

        alternatives_score = 0
        if option_count >= 2:
            alternatives_score += 4  # At least 2 options
        if option_count >= 3:
            alternatives_score += 2  # 3+ options
        if complete_options >= 2:
            alternatives_score += 4  # Thorough analysis
        scores['alternatives'] = min(10, alternatives_score)

        # 3. Information Score (0-10)
        # Heuristic based on context length and option details
        context_length = len(decision[3] or '')
        information_score = min(10, (context_length // 100) + (complete_options * 2))
        scores['information'] = information_score

        # 4. Values Score (0-10)
        # Based on stakeholder involvement and strategic alignment
        values_score = 0
        if decision[6]:  # stakeholders identified
            values_score += 5
        if 'strategic' in decision[1].lower() or 'strategic' in (decision[3] or '').lower():
            values_score += 5
        scores['values'] = min(10, values_score)

        # 5. Reasoning Score (0-10)
        # Based on chosen option having reasoning
        cursor.execute('''
            SELECT COUNT(*) FROM decision_options
            WHERE decision_id = ? AND is_chosen = 1 AND description IS NOT NULL
        ''', (decision_id,))
        has_reasoning = cursor.fetchone()[0] > 0

        reasoning_score = 10 if has_reasoning else 5
        scores['reasoning'] = reasoning_score

        # 6. Commitment Score (0-10)
        # Based on outcome tracking
        cursor.execute('SELECT COUNT(*) FROM decision_outcomes WHERE decision_id = ?', (decision_id,))
        has_outcome = cursor.fetchone()[0] > 0

        commitment_score = 10 if has_outcome else (7 if decision[7] == 'decided' else 3)
        scores['commitment'] = commitment_score

        # Total score
        total = sum(scores.values())
        scores['total'] = round(total, 1)

        # Store quality score
        cursor.execute('''
            INSERT INTO decision_quality (
                decision_id, frame_score, alternatives_score, information_score,
                values_score, reasoning_score, commitment_score, total_score, evaluated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            decision_id,
            scores['frame'],
            scores['alternatives'],
            scores['information'],
            scores['values'],
            scores['reasoning'],
            scores['commitment'],
            scores['total'],
            datetime.now().isoformat()
        ))

        conn.commit()
        conn.close()

        return scores

    def get_decision_summary(self, decision_id: int) -> str:
        """
        Generate decision summary document.

        Returns:
            Markdown summary
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Get decision
        cursor.execute('SELECT * FROM decisions WHERE id = ?', (decision_id,))
        decision = cursor.fetchone()
        if not decision:
            conn.close()
            return "Decision not found"

        summary = []
        summary.append(f"# Decision: {decision[2]}")
        summary.append(f"\n**Type**: {self.DECISION_TEMPLATES.get(decision[1], {}).get('name', decision[1])}")
        summary.append(f"**Status**: {decision[7] or 'pending'}")
        if decision[4]:
            summary.append(f"**Date**: {decision[4][:10]}")
        if decision[5]:
            summary.append(f"**Decided By**: {decision[5]}")
        summary.append("\n---\n")

        # Problem statement
        summary.append("## Problem Statement")
        summary.append(decision[3] if decision[3] else "*Not provided*")
        summary.append("")

        # Context
        if decision[3]:
            summary.append("## Context")
            summary.append(decision[3])
            summary.append("")

        # Options
        cursor.execute('''
            SELECT option_name, description, pros, cons, risks, is_chosen
            FROM decision_options WHERE decision_id = ?
        ''', (decision_id,))
        options = cursor.fetchall()

        if options:
            summary.append("## Options Considered\n")
            for i, opt in enumerate(options, 1):
                chosen = "✅ **CHOSEN**" if opt[5] else ""
                summary.append(f"### Option {i}: {opt[0]} {chosen}")
                if opt[1]:
                    summary.append(f"\n{opt[1]}\n")

                if opt[2]:
                    summary.append("**Pros:**")
                    for pro in json.loads(opt[2]):
                        summary.append(f"- {pro}")
                    summary.append("")

                if opt[3]:
                    summary.append("**Cons:**")
                    for con in json.loads(opt[3]):
                        summary.append(f"- {con}")
                    summary.append("")

                if opt[4]:
                    summary.append("**Risks:**")
                    for risk in json.loads(opt[4]):
                        summary.append(f"- {risk}")
                    summary.append("")

        # Outcome
        cursor.execute('''
            SELECT actual_outcome, success_level, lessons_learned, would_decide_again
            FROM decision_outcomes WHERE decision_id = ?
        ''', (decision_id,))
        outcome = cursor.fetchone()

        if outcome:
            summary.append("\n## Outcome")
            summary.append(f"\n**Success Level**: {outcome[1]}")
            summary.append(f"\n**Actual Outcome**:\n{outcome[0]}")

            if outcome[2]:
                summary.append(f"\n**Lessons Learned**:\n{outcome[2]}")

            if outcome[3] is not None:
                summary.append(f"\n**Would Decide Again**: {'Yes' if outcome[3] else 'No'}")

        # Quality score
        quality = self.calculate_quality_score(decision_id)
        if quality:
            summary.append("\n## Decision Quality Score")
            summary.append(f"\n**Total**: {quality['total']}/60")
            summary.append(f"- Frame: {quality['frame']}/10")
            summary.append(f"- Alternatives: {quality['alternatives']}/10")
            summary.append(f"- Information: {quality['information']}/10")
            summary.append(f"- Values: {quality['values']}/10")
            summary.append(f"- Reasoning: {quality['reasoning']}/10")
            summary.append(f"- Commitment: {quality['commitment']}/10")

        conn.close()

        return '\n'.join(summary)

    def get_decision_patterns(self) -> Dict:
        """
        Analyze decision patterns for learning.

        Returns:
            Pattern analysis dict
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        patterns = {}

        # Pattern 1: Decision type distribution
        cursor.execute('''
            SELECT decision_type, COUNT(*) FROM decisions
            GROUP BY decision_type
            ORDER BY COUNT(*) DESC
        ''')
        patterns['types'] = dict(cursor.fetchall())

        # Pattern 2: Average quality by type
        cursor.execute('''
            SELECT d.decision_type, AVG(q.total_score)
            FROM decisions d
            JOIN decision_quality q ON d.id = q.decision_id
            GROUP BY d.decision_type
        ''')
        patterns['quality_by_type'] = {k: round(v, 1) for k, v in cursor.fetchall()}

        # Pattern 3: Success rates by type
        cursor.execute('''
            SELECT d.decision_type, o.success_level, COUNT(*)
            FROM decisions d
            JOIN decision_outcomes o ON d.id = o.decision_id
            GROUP BY d.decision_type, o.success_level
        ''')
        success_data = cursor.fetchall()
        success_by_type = {}
        for dtype, level, count in success_data:
            if dtype not in success_by_type:
                success_by_type[dtype] = {}
            success_by_type[dtype][level] = count
        patterns['success_rates'] = success_by_type

        # Pattern 4: Average time to decision by type
        cursor.execute('''
            SELECT decision_type, AVG(
                julianday(reviewed_at) - julianday(decision_date)
            ) as avg_days
            FROM decisions
            WHERE reviewed_at IS NOT NULL
            GROUP BY decision_type
        ''')
        patterns['time_to_outcome'] = {k: round(v, 1) for k, v in cursor.fetchall()}

        conn.close()

        return patterns


def main():
    """CLI for decision intelligence agent"""
    import argparse

    parser = argparse.ArgumentParser(description="Decision Intelligence Agent")
    parser.add_argument('command', choices=['create', 'add-option', 'choose', 'outcome', 'summary', 'patterns'],
                       help='Command to execute')
    parser.add_argument('--id', type=int, help='Decision ID')
    parser.add_argument('--option-id', type=int, help='Option ID')
    parser.add_argument('--type', default='strategic', help='Decision type')
    parser.add_argument('--title', help='Decision title')
    parser.add_argument('--problem', help='Problem statement')
    parser.add_argument('--option', help='Option name')
    parser.add_argument('--outcome', help='Actual outcome')
    parser.add_argument('--success', choices=['exceeded', 'met', 'partial', 'missed', 'failed'],
                       help='Success level')

    args = parser.parse_args()

    # Initialize agent
    agent = DecisionIntelligenceAgent()

    if args.command == 'create':
        if not args.title or not args.problem:
            print("❌ Error: --title and --problem required")
            return
        decision_id = agent.create_decision(args.type, args.title, args.problem)
        print(f"✅ Decision created with ID: {decision_id}")

    elif args.command == 'add-option':
        if not args.id or not args.option:
            print("❌ Error: --id and --option required")
            return
        option_id = agent.add_option(args.id, args.option)
        print(f"✅ Option added with ID: {option_id}")

    elif args.command == 'choose':
        if not args.id or not args.option_id:
            print("❌ Error: --id and --option-id required")
            return
        agent.choose_option(args.id, args.option_id)

    elif args.command == 'outcome':
        if not args.id or not args.outcome or not args.success:
            print("❌ Error: --id, --outcome, and --success required")
            return
        agent.record_outcome(args.id, args.outcome, args.success)

    elif args.command == 'summary':
        if not args.id:
            print("❌ Error: --id required")
            return
        summary = agent.get_decision_summary(args.id)
        print(summary)

    elif args.command == 'patterns':
        patterns = agent.get_decision_patterns()
        print("\n📊 Decision Patterns:")
        print(f"\nTypes: {patterns['types']}")
        print(f"\nQuality by Type: {patterns['quality_by_type']}")
        print(f"\nSuccess Rates: {patterns['success_rates']}")
        print(f"\nTime to Outcome: {patterns['time_to_outcome']}")


if __name__ == '__main__':
    main()
