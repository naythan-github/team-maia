#!/usr/bin/env python3
"""
ServiceDesk Agent Quality Coaching System

Generates personalized quality coaching reports with RAG-sourced examples.

Usage:
    python3 servicedesk_agent_quality_coach.py --agent "John Smith" --period 30
    python3 servicedesk_agent_quality_coach.py --team "Cloud-Kirby" --period 7
"""

import sqlite3
import argparse
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from servicedesk_gpu_rag_indexer import GPURAGIndexer
import ollama


class AgentQualityCoach:
    """Generate coaching reports with RAG-sourced examples"""

    def __init__(self, db_path: str = None):
        from claude.tools.core.paths import DATA_DIR
        self.db_path = db_path or str(DATA_DIR / 'servicedesk_tickets.db')
        self.rag_indexer = GPURAGIndexer(db_path=self.db_path)
        self.llm_model = 'llama3.2:3b'

    def generate_agent_report(self, agent_name: str, period_days: int = 30) -> Dict:
        """
        Generate personalized coaching report for agent

        Args:
            agent_name: Agent's name (user_name in database)
            period_days: Analysis period in days (default: 30)

        Returns:
            {
                'agent_name': str,
                'team': str,
                'period_days': int,
                'scores': {...},
                'team_benchmarks': {...},
                'company_benchmarks': {...},
                'gaps': [...],
                'coaching_examples': [...],
                'trend': {...},
                'action_items': [...]
            }
        """

        print(f"\n{'='*70}")
        print(f"AGENT QUALITY COACHING REPORT")
        print(f"{'='*70}")
        print(f"Agent: {agent_name}")
        print(f"Period: Last {period_days} days")

        # 1. Get agent's quality scores
        print(f"\n📊 Analyzing agent scores...")
        agent_scores = self._get_agent_scores(agent_name, period_days)

        if not agent_scores:
            return {
                'error': f"No quality analysis found for agent '{agent_name}' in last {period_days} days"
            }

        # 2. Get team/company benchmarks
        team = agent_scores.get('team', 'Unknown')
        print(f"   Team: {team}")

        team_benchmarks = self._get_team_benchmarks(team, period_days)
        company_benchmarks = self._get_company_benchmarks(period_days)

        # 3. Identify gaps (dimensions below team average)
        gaps = self._identify_gaps(agent_scores, team_benchmarks)
        print(f"   Gap areas identified: {len(gaps)}")

        # 4. RAG search: Find excellent examples for gap areas
        print(f"\n🔍 Finding excellent examples from RAG database...")
        coaching_examples = []
        for gap in gaps:
            examples = self._find_coaching_examples(gap, team)
            agent_poor_example = self._find_agent_poor_example(agent_name, gap['dimension'])

            coaching_examples.append({
                'dimension': gap['dimension'],
                'agent_score': gap['agent_score'],
                'team_avg': gap['team_avg'],
                'excellent_examples': examples[:3],  # Top 3
                'agent_poor_example': agent_poor_example
            })

        # 5. Generate LLM coaching recommendations
        print(f"\n🤖 Generating coaching with llama3.2:3b...")
        coaching = self._generate_llm_coaching(agent_scores, gaps, coaching_examples)

        # 6. Get trend analysis (month-over-month)
        trend = self._get_trend_analysis(agent_name, period_days)

        # 7. Generate action items
        action_items = self._generate_action_items(gaps, coaching_examples)

        report = {
            'agent_name': agent_name,
            'team': team,
            'period_days': period_days,
            'scores': agent_scores,
            'team_benchmarks': team_benchmarks,
            'company_benchmarks': company_benchmarks,
            'gaps': gaps,
            'coaching_examples': coaching_examples,
            'trend': trend,
            'action_items': action_items,
            'llm_coaching': coaching,
            'generated_at': datetime.now().isoformat()
        }

        print(f"\n✅ Coaching report generated successfully")

        return report

    def _get_agent_scores(self, agent_name: str, period_days: int) -> Optional[Dict]:
        """Get agent's average quality scores for period"""

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Get scores from last N days
        cutoff_date = (datetime.now() - timedelta(days=period_days)).isoformat()

        # Note: comment_quality has all fields we need (no JOIN required)
        query = """
            SELECT
                team,
                AVG(professionalism_score) as avg_professionalism,
                AVG(clarity_score) as avg_clarity,
                AVG(empathy_score) as avg_empathy,
                AVG(actionability_score) as avg_actionability,
                AVG(quality_score) as avg_quality,
                COUNT(*) as comment_count
            FROM comment_quality
            WHERE user_name = ?
              AND created_time >= ?
            GROUP BY team
        """

        cursor.execute(query, (agent_name, cutoff_date))
        row = cursor.fetchone()
        conn.close()

        if not row:
            return None

        return {
            'team': row[0],
            'professionalism': round(row[1], 2) if row[1] else 0,
            'clarity': round(row[2], 2) if row[2] else 0,
            'empathy': round(row[3], 2) if row[3] else 0,
            'actionability': round(row[4], 2) if row[4] else 0,
            'overall': round(row[5], 2) if row[5] else 0,
            'comment_count': row[6]
        }

    def _get_team_benchmarks(self, team: str, period_days: int) -> Dict:
        """Get team average scores"""

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cutoff_date = (datetime.now() - timedelta(days=period_days)).isoformat()

        query = """
            SELECT
                AVG(professionalism_score) as avg_professionalism,
                AVG(clarity_score) as avg_clarity,
                AVG(empathy_score) as avg_empathy,
                AVG(actionability_score) as avg_actionability,
                AVG(quality_score) as avg_quality
            FROM comment_quality
            WHERE team = ?
              AND created_time >= ?
        """

        cursor.execute(query, (team, cutoff_date))
        row = cursor.fetchone()
        conn.close()

        if not row or not row[0]:
            # Return neutral benchmarks if no team data
            return {
                'professionalism': 3.0,
                'clarity': 3.0,
                'empathy': 3.0,
                'actionability': 3.0,
                'overall': 3.0
            }

        return {
            'professionalism': round(row[0], 2),
            'clarity': round(row[1], 2),
            'empathy': round(row[2], 2),
            'actionability': round(row[3], 2),
            'overall': round(row[4], 2)
        }

    def _get_company_benchmarks(self, period_days: int) -> Dict:
        """Get company-wide average scores"""

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cutoff_date = (datetime.now() - timedelta(days=period_days)).isoformat()

        query = """
            SELECT
                AVG(professionalism_score) as avg_professionalism,
                AVG(clarity_score) as avg_clarity,
                AVG(empathy_score) as avg_empathy,
                AVG(actionability_score) as avg_actionability,
                AVG(quality_score) as avg_quality
            FROM comment_quality
            WHERE created_time >= ?
        """

        cursor.execute(query, (cutoff_date,))
        row = cursor.fetchone()
        conn.close()

        if not row or not row[0]:
            return {
                'professionalism': 3.0,
                'clarity': 3.0,
                'empathy': 3.0,
                'actionability': 3.0,
                'overall': 3.0
            }

        return {
            'professionalism': round(row[0], 2),
            'clarity': round(row[1], 2),
            'empathy': round(row[2], 2),
            'actionability': round(row[3], 2),
            'overall': round(row[4], 2)
        }

    def _identify_gaps(self, agent_scores: Dict, team_benchmarks: Dict) -> List[Dict]:
        """Identify dimensions where agent is below team average"""

        gaps = []
        dimensions = ['professionalism', 'clarity', 'empathy', 'actionability']

        for dim in dimensions:
            agent_score = agent_scores.get(dim, 0)
            team_avg = team_benchmarks.get(dim, 3.0)

            if agent_score < team_avg - 0.3:  # 0.3 point threshold
                gaps.append({
                    'dimension': dim,
                    'agent_score': agent_score,
                    'team_avg': team_avg,
                    'gap': round(team_avg - agent_score, 2)
                })

        # Sort by gap size (largest first)
        gaps.sort(key=lambda x: x['gap'], reverse=True)

        return gaps

    def _find_coaching_examples(self, gap: Dict, team: str) -> List[Dict]:
        """
        Find excellent examples using RAG quality search

        Args:
            gap: {'dimension': 'empathy', 'agent_score': 2.1, 'team_avg': 3.2}
            team: Agent's team name

        Returns:
            List of excellent examples for coaching
        """

        dimension = gap['dimension']

        # Build semantic query
        query_text = f"excellent {dimension} customer communication"

        # Search parameters based on dimension
        search_params = {
            'query_text': query_text,
            'quality_tier': 'excellent',
            'team': team,  # Same team for relevance
            'limit': 10
        }

        # Add dimension-specific score filter
        if dimension == 'empathy':
            search_params['min_empathy_score'] = 4
        elif dimension == 'clarity':
            search_params['min_clarity_score'] = 4

        # Execute RAG search
        try:
            results = self.rag_indexer.search_by_quality(**search_params)

            if not results['documents'][0]:
                # Fall back to any excellent examples if none from same team
                search_params['team'] = None
                results = self.rag_indexer.search_by_quality(**search_params)

            # Format results
            examples = []
            for i, doc in enumerate(results['documents'][0][:5]):
                meta = results['metadatas'][0][i]
                examples.append({
                    'text': doc,
                    'user_name': meta.get('user_name', 'Unknown'),
                    'ticket_id': meta.get('ticket_id', 'Unknown'),
                    'score': int(meta.get(f'{dimension}_score', 5)),
                    'quality_score': float(meta.get('quality_score', 5.0)),
                    'created_time': meta.get('created_time', '')
                })

            return examples

        except Exception as e:
            print(f"   ⚠️  RAG search failed for {dimension}: {e}")
            return []

    def _find_agent_poor_example(self, agent_name: str, dimension: str) -> Optional[Dict]:
        """Find a poor example from agent for contrast"""

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Get a low-scoring comment from this agent for this dimension
        query = f"""
            SELECT
                comment_id,
                ticket_id,
                cleaned_text,
                {dimension}_score,
                quality_score,
                created_time
            FROM comment_quality
            WHERE user_name = ?
              AND {dimension}_score <= 2
            ORDER BY {dimension}_score ASC
            LIMIT 1
        """

        cursor.execute(query, (agent_name,))
        row = cursor.fetchone()
        conn.close()

        if not row:
            return None

        return {
            'comment_id': row[0],
            'ticket_id': row[1],
            'text': row[2],
            'score': row[3],
            'quality_score': row[4],
            'created_time': row[5]
        }

    def _generate_llm_coaching(
        self,
        agent_scores: Dict,
        gaps: List[Dict],
        coaching_examples: List[Dict]
    ) -> str:
        """
        Use LLM to generate specific coaching recommendations

        Uses Ollama llama3.2:3b for local generation
        """

        if not gaps:
            return "Great work! All quality dimensions are at or above team average. Keep up the excellent communication!"

        # Build prompt with agent scores + examples
        gap_summary = "\n".join([
            f"- {gap['dimension'].title()}: {gap['agent_score']:.1f}/5 (Team avg: {gap['team_avg']:.1f}/5, Gap: -{gap['gap']:.1f})"
            for gap in gaps[:3]  # Top 3 gaps
        ])

        # Get primary gap example
        primary_gap = gaps[0]
        primary_examples = [ex for ex in coaching_examples if ex['dimension'] == primary_gap['dimension']]

        example_text = ""
        if primary_examples and primary_examples[0]['excellent_examples']:
            ex = primary_examples[0]['excellent_examples'][0]
            example_text = f"\n\nEXCELLENT EXAMPLE (for {primary_gap['dimension']}):\n{ex['text'][:300]}..."

        prompt = f"""You are a ServiceDesk quality coach. Generate specific, actionable coaching for this agent.

AGENT SCORES (Last 30 Days):
- Professionalism: {agent_scores['professionalism']:.1f}/5
- Clarity: {agent_scores['clarity']:.1f}/5
- Empathy: {agent_scores['empathy']:.1f}/5
- Actionability: {agent_scores['actionability']:.1f}/5

PRIMARY GAPS (Below Team Average):
{gap_summary}

{example_text}

Generate coaching that:
1. Focuses on the PRIMARY gap ({primary_gap['dimension']})
2. Explains WHY this dimension matters (customer impact)
3. Provides 3 SPECIFIC techniques to improve
4. Uses encouraging, constructive tone (not critical)

Keep response under 300 words, focus on actionable techniques."""

        try:
            response = ollama.chat(
                model=self.llm_model,
                messages=[{'role': 'user', 'content': prompt}],
                options={'temperature': 0.7}
            )

            return response['message']['content']

        except Exception as e:
            print(f"   ⚠️  LLM coaching generation failed: {e}")
            return self._generate_template_coaching(gaps)

    def _generate_template_coaching(self, gaps: List[Dict]) -> str:
        """Fallback: Template-based coaching when LLM fails"""

        if not gaps:
            return "All quality dimensions are at or above team average. Excellent work!"

        primary_gap = gaps[0]['dimension']

        templates = {
            'empathy': """**Improve Empathy**

Your empathy scores could be stronger. Customers want to feel heard and understood.

**Key Techniques**:
1. **Acknowledge frustration**: Start with "I understand how frustrating this must be..."
2. **Show context awareness**: "Especially during busy workdays..." or "I know password issues can be disruptive..."
3. **Express genuine care**: "I want to make sure this is fully resolved for you"
4. **Offer proactive support**: "Please let me know if you need anything else"

**Example opening**: "I understand how frustrating password issues can be, especially when you're trying to get work done. Let me help resolve this for you right away."
""",
            'clarity': """**Improve Clarity**

Your responses could be more structured and clear. Customers appreciate organized information.

**Key Techniques**:
1. **Use structure**: Issue → Status → Next Steps
2. **Include specific timelines**: Use "within 24 hours" not "soon"
3. **Break down complex steps**: Use bullet points or numbered lists
4. **Confirm understanding**: "Does this make sense?" or "Let me know if you need clarification"

**Example structure**:
- Issue identified: [what's wrong]
- Current status: [what's been done]
- Next steps: [what will happen, when]
""",
            'actionability': """**Improve Actionability**

Your responses need clearer next steps. Customers want to know what happens next.

**Key Techniques**:
1. **Always include "Next Steps"**: Tell customers what to do or what you'll do
2. **Provide specific timelines**: "I'll follow up by 2pm tomorrow"
3. **Confirm resolution**: Don't just say "done" - verify it works
4. **Offer follow-up**: "I'll check back in 24 hours to ensure this is resolved"

**Example closing**: "Next steps: I'll monitor this overnight and follow up at 9am tomorrow. If you see any issues before then, please let me know."
""",
            'professionalism': """**Improve Professionalism**

Your communication could be more polished and professional.

**Key Techniques**:
1. **Proofread before sending**: Check spelling, grammar, punctuation
2. **Use professional greetings**: "Hi [Name]," not "Hey"
3. **Avoid jargon**: Explain technical terms in simple language
4. **Be consistent**: Use proper capitalization and formatting

**Example**: Instead of "fixed the vpn thing", write "I've resolved the VPN connectivity issue. Your connection should be stable now."
"""
        }

        return templates.get(primary_gap, "Focus on improving quality communication with specific examples and clear next steps.")

    def _get_trend_analysis(self, agent_name: str, period_days: int) -> Dict:
        """Get month-over-month trend"""

        # Simple trend: compare current period vs previous period
        current = self._get_agent_scores(agent_name, period_days)

        if not current:
            return {}

        # Get previous period scores
        previous = self._get_agent_scores_for_period(
            agent_name,
            datetime.now() - timedelta(days=period_days*2),
            datetime.now() - timedelta(days=period_days)
        )

        if not previous:
            return {'current': current, 'trend': 'insufficient_data'}

        # Calculate trend
        trend = {
            'current_quality': current['overall'],
            'previous_quality': previous['overall'],
            'change': round(current['overall'] - previous['overall'], 2),
            'change_pct': round((current['overall'] - previous['overall']) / previous['overall'] * 100, 1) if previous['overall'] > 0 else 0,
            'direction': '↗ improving' if current['overall'] > previous['overall'] else '↘ declining' if current['overall'] < previous['overall'] else '→ stable'
        }

        return trend

    def _get_agent_scores_for_period(self, agent_name: str, start_date: datetime, end_date: datetime) -> Optional[Dict]:
        """Get agent scores for specific date range"""

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        query = """
            SELECT
                team,
                AVG(professionalism_score) as avg_professionalism,
                AVG(clarity_score) as avg_clarity,
                AVG(empathy_score) as avg_empathy,
                AVG(actionability_score) as avg_actionability,
                AVG(quality_score) as avg_quality,
                COUNT(*) as comment_count
            FROM comment_quality
            WHERE user_name = ?
              AND created_time >= ?
              AND created_time < ?
            GROUP BY team
        """

        cursor.execute(query, (agent_name, start_date.isoformat(), end_date.isoformat()))
        row = cursor.fetchone()
        conn.close()

        if not row:
            return None

        return {
            'team': row[0],
            'professionalism': round(row[1], 2) if row[1] else 0,
            'clarity': round(row[2], 2) if row[2] else 0,
            'empathy': round(row[3], 2) if row[3] else 0,
            'actionability': round(row[4], 2) if row[4] else 0,
            'overall': round(row[5], 2) if row[5] else 0,
            'comment_count': row[6]
        }

    def _generate_action_items(self, gaps: List[Dict], examples: List[Dict]) -> List[str]:
        """Generate specific action items for agent"""

        action_items = []

        if not gaps:
            return ["Continue excellent quality communication - no action items needed!"]

        for gap in gaps[:2]:  # Top 2 gaps
            dim = gap['dimension']

            if dim == 'empathy':
                action_items.extend([
                    f"Review 3 excellent empathy examples from your team",
                    f"Use 'I understand...' opener for next 10 customer responses",
                    f"Acknowledge customer frustration before stating resolution"
                ])
            elif dim == 'clarity':
                action_items.extend([
                    f"Structure responses: Issue → Status → Next Steps",
                    f"Include specific timelines (not 'soon' or 'ASAP')",
                    f"Use bullet points for multi-step instructions"
                ])
            elif dim == 'actionability':
                action_items.extend([
                    f"Always include 'Next Steps' section in responses",
                    f"Provide specific timelines for follow-up",
                    f"Confirm resolution before closing ticket"
                ])
            elif dim == 'professionalism':
                action_items.extend([
                    f"Proofread all customer-facing comments before sending",
                    f"Use professional greetings ('Hi [Name],' not 'Hey')",
                    f"Avoid technical jargon without explanation"
                ])

        return action_items[:5]  # Top 5 action items

    def format_report_markdown(self, report: Dict) -> str:
        """Format coaching report as markdown"""

        if report.get('error'):
            return f"# Error\n\n{report['error']}"

        md = f"""# Quality Coaching Report - {report['agent_name']}

**Team**: {report['team']}
**Period**: Last {report['period_days']} days
**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M')}

---

## 📊 Your Quality Scores

| Dimension | Your Score | Team Avg | Company Avg | Status |
|-----------|------------|----------|-------------|--------|
| Professionalism | {report['scores']['professionalism']:.1f}/5 | {report['team_benchmarks']['professionalism']:.1f}/5 | {report['company_benchmarks']['professionalism']:.1f}/5 | {self._status_emoji(report['scores']['professionalism'], report['team_benchmarks']['professionalism'])} |
| Clarity | {report['scores']['clarity']:.1f}/5 | {report['team_benchmarks']['clarity']:.1f}/5 | {report['company_benchmarks']['clarity']:.1f}/5 | {self._status_emoji(report['scores']['clarity'], report['team_benchmarks']['clarity'])} |
| Empathy | {report['scores']['empathy']:.1f}/5 | {report['team_benchmarks']['empathy']:.1f}/5 | {report['company_benchmarks']['empathy']:.1f}/5 | {self._status_emoji(report['scores']['empathy'], report['team_benchmarks']['empathy'])} |
| Actionability | {report['scores']['actionability']:.1f}/5 | {report['team_benchmarks']['actionability']:.1f}/5 | {report['company_benchmarks']['actionability']:.1f}/5 | {self._status_emoji(report['scores']['actionability'], report['team_benchmarks']['actionability'])} |

**Overall Quality**: {report['scores']['overall']:.1f}/5 (Team: {report['team_benchmarks']['overall']:.1f}/5)
**Comments Analyzed**: {report['scores']['comment_count']}

---

## 💡 Coaching Recommendations

{report['llm_coaching']}

---

## 📋 Action Items

"""
        for i, action in enumerate(report['action_items'], 1):
            md += f"{i}. [ ] {action}\n"

        # Add trend if available
        if report.get('trend') and report['trend'].get('direction'):
            trend = report['trend']
            md += f"""
---

## 📈 Your Progress

**Quality Trend**: {trend['direction']}
- Current period: {trend['current_quality']:.1f}/5
- Previous period: {trend['previous_quality']:.1f}/5
- Change: {trend['change']:+.1f} ({trend['change_pct']:+.1f}%)
"""

        md += f"""
---

*Generated by ServiceDesk Quality Coaching System*
*Questions? Contact your team lead or ServiceDesk Manager*
"""

        return md

    @staticmethod
    def _status_emoji(agent_score: float, team_avg: float) -> str:
        """Generate status emoji based on comparison"""
        diff = agent_score - team_avg
        if diff >= 0.5:
            return "✅ ABOVE AVERAGE"
        elif diff <= -0.5:
            return "🚨 NEEDS IMPROVEMENT"
        else:
            return "⚠️ SLIGHTLY BELOW" if diff < 0 else "✅ ON TARGET"


def main():
    parser = argparse.ArgumentParser(description='Generate quality coaching reports')
    parser.add_argument('--agent', required=True, help='Agent name (user_name)')
    parser.add_argument('--period', type=int, default=30, help='Period in days (default: 30)')
    parser.add_argument('--output', type=str, help='Output markdown file path')

    args = parser.parse_args()

    coach = AgentQualityCoach()
    report = coach.generate_agent_report(args.agent, period_days=args.period)

    if report.get('error'):
        print(f"\n❌ Error: {report['error']}")
        return

    markdown = coach.format_report_markdown(report)

    # Save to file if specified, otherwise print
    if args.output:
        with open(args.output, 'w') as f:
            f.write(markdown)
        print(f"\n✅ Coaching report saved: {args.output}")
    else:
        print(f"\n{markdown}")


if __name__ == '__main__':
    main()
