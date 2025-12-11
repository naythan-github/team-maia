#!/usr/bin/env python3
"""
ServiceDesk Quality Monitoring Service

Integrates Phase 2 Quality Intelligence with Phase 130 Operations Intelligence.

Features:
- Automatic quality analysis of new comments
- Real-time quality score tracking
- Quality degradation alerts
- Auto-create ops intelligence insights from quality trends
- Pattern detection (team-wide quality drops, recurring issues)

Usage:
    # Monitor quality for recent comments
    python3 servicedesk_quality_monitoring.py --monitor --days 7

    # Generate quality insights for ops intelligence
    python3 servicedesk_quality_monitoring.py --generate-insights --days 30

    # Check for quality degradation alerts
    python3 servicedesk_quality_monitoring.py --check-alerts

Phase: 3.1 (Quality Intelligence Roadmap)
Author: Maia (ServiceDesk Manager Agent)
Date: 2025-10-18
"""

import argparse
import sqlite3
import json
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from servicedesk_operations_intelligence import ServiceDeskOpsIntelligence, OperationalInsight, Recommendation
from servicedesk_realtime_quality_assistant import RealtimeQualityAssistant


class QualityMonitoringService:
    """
    Monitor ServiceDesk comment quality and integrate with Ops Intelligence
    """

    def __init__(
        self,
        tickets_db_path: str = None,
        ops_intel_db_path: str = None
    ):
        from claude.tools.core.paths import DATA_DIR
        self.tickets_db_path = tickets_db_path or str(DATA_DIR / 'servicedesk_tickets.db')
        self.ops_intel = ServiceDeskOpsIntelligence(ops_intel_db_path) if ops_intel_db_path else ServiceDeskOpsIntelligence()
        self.quality_assistant = RealtimeQualityAssistant()

    def monitor_recent_quality(self, days: int = 7) -> Dict:
        """
        Monitor quality for comments in the last N days

        Returns quality statistics and identifies trends
        """

        print(f"\n{'='*70}")
        print(f"QUALITY MONITORING: Last {days} Days")
        print(f"{'='*70}")

        conn = sqlite3.connect(self.tickets_db_path)
        cursor = conn.cursor()

        # Get comments from last N days
        cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()

        query = """
            SELECT
                comment_id,
                user_name,
                team,
                comment_text,
                created_time
            FROM comments
            WHERE created_time >= ?
              AND comment_text IS NOT NULL
              AND comment_text != ''
              AND LENGTH(comment_text) > 20
            ORDER BY created_time DESC
            LIMIT 100
        """

        cursor.execute(query, (cutoff_date,))
        comments = cursor.fetchall()
        conn.close()

        print(f"\n📊 Found {len(comments)} comments to analyze")

        # Analyze quality for each comment (sample)
        quality_scores = []
        agent_scores = {}
        team_scores = {}

        for comment_id, user_name, team, comment_text, created_time in comments:
            # Analyze quality
            result = self.quality_assistant.analyze_comment(comment_text)
            scores = result.get('scores', {})

            quality_scores.append({
                'comment_id': comment_id,
                'user_name': user_name,
                'team': team,
                'created_time': created_time,
                'overall_score': scores.get('overall', 0),
                'professionalism': scores.get('professionalism', 0),
                'clarity': scores.get('clarity', 0),
                'empathy': scores.get('empathy', 0),
                'actionability': scores.get('actionability', 0),
                'quality_tier': result.get('quality_tier', 'N/A')
            })

            # Aggregate by agent
            if user_name not in agent_scores:
                agent_scores[user_name] = []
            agent_scores[user_name].append(scores.get('overall', 0))

            # Aggregate by team
            if team not in team_scores:
                team_scores[team] = []
            team_scores[team].append(scores.get('overall', 0))

        # Calculate statistics
        overall_avg = sum(s['overall_score'] for s in quality_scores) / len(quality_scores) if quality_scores else 0

        agent_avgs = {
            agent: sum(scores) / len(scores)
            for agent, scores in agent_scores.items()
        }

        team_avgs = {
            team: sum(scores) / len(scores)
            for team, scores in team_scores.items()
        }

        print(f"\n📈 Quality Statistics:")
        print(f"   Overall Average: {overall_avg:.2f}/5")
        print(f"   Total Comments: {len(quality_scores)}")
        print(f"   Agents Analyzed: {len(agent_scores)}")
        print(f"   Teams Analyzed: {len(team_scores)}")

        return {
            'period_days': days,
            'total_comments': len(quality_scores),
            'overall_avg': overall_avg,
            'agent_scores': agent_avgs,
            'team_scores': team_avgs,
            'quality_scores': quality_scores
        }

    def check_quality_degradation(self, days: int = 30, threshold: float = 3.0) -> List[Dict]:
        """
        Check for quality degradation (agents or teams below threshold)

        Returns list of alerts
        """

        print(f"\n{'='*70}")
        print(f"QUALITY DEGRADATION CHECK")
        print(f"{'='*70}")
        print(f"Period: Last {days} days")
        print(f"Threshold: {threshold}/5")

        # Monitor recent quality
        stats = self.monitor_recent_quality(days)

        alerts = []

        # Check agent quality
        for agent, avg_score in stats['agent_scores'].items():
            if avg_score < threshold:
                alerts.append({
                    'type': 'agent_quality_degradation',
                    'severity': 'high' if avg_score < 2.5 else 'medium',
                    'agent': agent,
                    'score': avg_score,
                    'threshold': threshold,
                    'description': f"{agent} quality score ({avg_score:.2f}) below threshold ({threshold})"
                })

        # Check team quality
        for team, avg_score in stats['team_scores'].items():
            if avg_score < threshold:
                alerts.append({
                    'type': 'team_quality_degradation',
                    'severity': 'high' if avg_score < 2.5 else 'medium',
                    'team': team,
                    'score': avg_score,
                    'threshold': threshold,
                    'description': f"{team} quality score ({avg_score:.2f}) below threshold ({threshold})"
                })

        print(f"\n🚨 Quality Alerts: {len(alerts)}")
        for alert in alerts:
            print(f"   {alert['severity'].upper()}: {alert['description']}")

        return alerts

    def generate_ops_insights(self, days: int = 30) -> List[int]:
        """
        Generate Operations Intelligence insights from quality trends

        Creates insights in the ops_intel database for:
        - Quality degradation patterns
        - Team-wide quality issues
        - Agent skill gaps

        Returns list of created insight IDs
        """

        print(f"\n{'='*70}")
        print(f"GENERATING OPS INTELLIGENCE INSIGHTS")
        print(f"{'='*70}")

        # Check for quality degradation
        alerts = self.check_quality_degradation(days)

        created_insight_ids = []

        # Create insights for each alert
        for alert in alerts:
            if alert['type'] == 'agent_quality_degradation':
                # Create skill_gap insight
                insight = OperationalInsight(
                    insight_type='skill_gap',
                    title=f"Quality degradation: {alert['agent']} below threshold",
                    description=f"{alert['agent']} has average quality score of {alert['score']:.2f}/5 (threshold: {alert['threshold']}/5) over last {days} days. Requires coaching or training intervention.",
                    identified_date=datetime.now().strftime('%Y-%m-%d'),
                    severity=alert['severity'],
                    affected_clients='[]',  # Would need to fetch from tickets
                    affected_categories='[]',
                    affected_ticket_ids='[]',
                    root_cause=f"Agent quality scores consistently below acceptable threshold. Possible causes: lack of training, high workload, unclear guidelines, or skill gap.",
                    business_impact=f"Poor quality communication impacts customer satisfaction and may lead to escalations or complaints.",
                    status='active'
                )

                # Save to ops intelligence
                insight_id = self.ops_intel.create_insight(insight)
                created_insight_ids.append(insight_id)

                print(f"\n✅ Created insight #{insight_id}: {insight.title}")

                # Create coaching recommendation
                recommendation = Recommendation(
                    insight_id=insight_id,
                    recommendation_type='training',
                    title=f"Provide quality coaching to {alert['agent']}",
                    description=f"Generate personalized coaching report using Agent Quality Coach and schedule 1:1 session to review feedback and improvement areas.",
                    estimated_effort='1 hour',
                    estimated_impact=f"Improve {alert['agent']} quality score from {alert['score']:.2f} to 3.5+ within 30 days",
                    priority='high' if alert['severity'] == 'high' else 'medium',
                    status='proposed',
                    assigned_to='Team Lead',
                    due_date=(datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d')
                )

                rec_id = self.ops_intel.create_recommendation(recommendation)
                print(f"   ✅ Created recommendation #{rec_id}: {recommendation.title}")

            elif alert['type'] == 'team_quality_degradation':
                # Create team-wide insight
                insight = OperationalInsight(
                    insight_type='skill_gap',
                    title=f"Team quality degradation: {alert['team']}",
                    description=f"{alert['team']} has average quality score of {alert['score']:.2f}/5 (threshold: {alert['threshold']}/5) over last {days} days. Team-wide intervention needed.",
                    identified_date=datetime.now().strftime('%Y-%m-%d'),
                    severity='high',  # Team issues are high severity
                    affected_clients='[]',
                    affected_categories='[]',
                    affected_ticket_ids='[]',
                    root_cause=f"Team-wide quality issue suggests systemic problem: inadequate training, unclear processes, or resource constraints.",
                    business_impact=f"Team-wide quality degradation impacts multiple customers and increases risk of SLA breaches and client churn.",
                    status='active'
                )

                insight_id = self.ops_intel.create_insight(insight)
                created_insight_ids.append(insight_id)

                print(f"\n✅ Created insight #{insight_id}: {insight.title}")

                # Create team training recommendation
                recommendation = Recommendation(
                    insight_id=insight_id,
                    recommendation_type='training',
                    title=f"Team training session for {alert['team']}",
                    description=f"Conduct team workshop on quality communication best practices. Use Best Practice Library examples and address common gaps.",
                    estimated_effort='4 hours (prep + session)',
                    estimated_impact=f"Improve {alert['team']} quality score from {alert['score']:.2f} to 3.5+ within 30 days",
                    priority='high',
                    status='proposed',
                    assigned_to='ServiceDesk Manager',
                    due_date=(datetime.now() + timedelta(days=14)).strftime('%Y-%m-%d')
                )

                rec_id = self.ops_intel.create_recommendation(recommendation)
                print(f"   ✅ Created recommendation #{rec_id}: {recommendation.title}")

        print(f"\n✅ Created {len(created_insight_ids)} ops intelligence insights")
        return created_insight_ids

    def track_quality_outcomes(self, recommendation_id: int, days: int = 30) -> Dict:
        """
        Track quality improvement outcomes after coaching intervention

        Measures before/after quality scores to validate recommendation effectiveness
        """

        print(f"\n{'='*70}")
        print(f"TRACKING QUALITY OUTCOMES")
        print(f"{'='*70}")
        print(f"Recommendation ID: {recommendation_id}")

        # Get recommendation details
        recommendation = self.ops_intel.get_recommendation(recommendation_id)

        if not recommendation:
            print(f"❌ Recommendation #{recommendation_id} not found")
            return {}

        print(f"Title: {recommendation.title}")
        print(f"Status: {recommendation.status}")

        # TODO: Implement outcome tracking
        # - Get baseline quality score (before intervention)
        # - Get current quality score (after intervention)
        # - Calculate improvement percentage
        # - Save to outcomes table

        print(f"\n⚠️  Outcome tracking implementation pending")
        return {}


def main():
    parser = argparse.ArgumentParser(description='ServiceDesk Quality Monitoring Service')

    # Monitoring commands
    parser.add_argument('--monitor', action='store_true',
                       help='Monitor recent comment quality')
    parser.add_argument('--days', type=int, default=7,
                       help='Number of days to analyze (default: 7)')

    # Alert commands
    parser.add_argument('--check-alerts', action='store_true',
                       help='Check for quality degradation alerts')
    parser.add_argument('--threshold', type=float, default=3.0,
                       help='Quality threshold for alerts (default: 3.0)')

    # Ops intelligence integration
    parser.add_argument('--generate-insights', action='store_true',
                       help='Generate ops intelligence insights from quality trends')

    # Outcome tracking
    parser.add_argument('--track-outcomes', type=int,
                       help='Track quality outcomes for recommendation ID')

    args = parser.parse_args()

    # Initialize service
    service = QualityMonitoringService()

    # Execute commands
    if args.monitor:
        service.monitor_recent_quality(args.days)

    elif args.check_alerts:
        service.check_quality_degradation(args.days, args.threshold)

    elif args.generate_insights:
        service.generate_ops_insights(args.days)

    elif args.track_outcomes:
        service.track_quality_outcomes(args.track_outcomes, args.days)

    else:
        parser.print_help()


if __name__ == '__main__':
    main()
