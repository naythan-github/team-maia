#!/usr/bin/env python3
"""
SDM Agent Operations Intelligence Integration

Helper module for ServiceDesk Manager Agent to automatically use
hybrid operations intelligence system during complaint analysis.

Phase: 130.2 - SDM Agent Integration
Created: 2025-10-18
"""

import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent))

from servicedesk_ops_intel_hybrid import ServiceDeskOpsIntelHybrid
from servicedesk_operations_intelligence import (
    OperationalInsight,
    Recommendation,
    ActionTaken,
    Outcome,
    Learning
)


class SDMAgentOpsIntelHelper:
    """
    Integration helper for SDM Agent to use operations intelligence.

    Provides simplified interface for common SDM Agent workflows.
    """

    def __init__(self):
        """Initialize hybrid intelligence system"""
        self.ops_intel = ServiceDeskOpsIntelHybrid()

    def start_complaint_analysis(
        self,
        complaint_description: str,
        affected_clients: List[str],
        affected_categories: List[str],
        ticket_ids: List[int] = None
    ) -> Dict:
        """
        Step 1: Start complaint analysis workflow.

        Automatically:
        - Checks for similar past patterns
        - Suggests past recommendations if found
        - Returns context for SDM Agent to use

        Args:
            complaint_description: Natural language description of complaint
            affected_clients: List of client names
            affected_categories: List of categories (Azure, Exchange, etc.)
            ticket_ids: Optional list of ticket IDs

        Returns:
            Dict with similar_pattern (if found) and suggested_actions
        """

        print(f"\n🔍 Checking for similar past patterns...")

        # Create temporary insight for pattern matching
        temp_insight = OperationalInsight(
            insight_type='temp',
            title=complaint_description[:100],
            description=complaint_description,
            identified_date=datetime.now().isoformat(),
            affected_clients=str(affected_clients),
            affected_categories=str(affected_categories)
        )

        # Check for similar patterns
        pattern_match = self.ops_intel.check_similar_patterns(temp_insight, similarity_threshold=0.85)

        result = {
            'has_similar_pattern': False,
            'pattern_match': None,
            'suggested_recommendations': [],
            'past_outcomes': []
        }

        if pattern_match:
            result['has_similar_pattern'] = True
            result['pattern_match'] = pattern_match['similar_insight']
            result['suggested_recommendations'] = pattern_match.get('past_recommendations', [])
            result['past_outcomes'] = pattern_match.get('outcomes', [])

            print(f"   ⚠️  SIMILAR PATTERN FOUND (Similarity: {pattern_match['similarity_score']:.1%})")
            print(f"   📌 Past Case: {pattern_match['similar_insight']['title']}")

            if result['past_outcomes']:
                for outcome in result['past_outcomes']:
                    print(f"   📈 Past Success: {outcome['metric_type']} improved {outcome['improvement_pct']:.1f}%")

            if result['suggested_recommendations']:
                print(f"   💡 Suggested Actions: {len(result['suggested_recommendations'])} recommendations from past case")
        else:
            print(f"   ✅ No similar patterns found - this appears to be a new issue")

        return result

    def record_insight(
        self,
        insight_type: str,
        title: str,
        description: str,
        severity: str,
        affected_clients: List[str],
        affected_categories: List[str],
        affected_ticket_ids: List[int],
        root_cause: str,
        business_impact: str
    ) -> int:
        """
        Step 2: Record identified insight after analysis.

        Automatically embeds in ChromaDB for future semantic search.

        Args:
            insight_type: complaint_pattern, escalation_bottleneck, fcr_opportunity, skill_gap, client_at_risk
            title: Short title
            description: Detailed description
            severity: critical, high, medium, low
            affected_clients: List of client names
            affected_categories: List of categories
            affected_ticket_ids: List of ticket IDs
            root_cause: 5-Whys root cause analysis result
            business_impact: Impact statement

        Returns:
            insight_id
        """

        insight = OperationalInsight(
            insight_type=insight_type,
            title=title,
            description=description,
            identified_date=datetime.now().isoformat(),
            severity=severity,
            affected_clients=str(affected_clients),
            affected_categories=str(affected_categories),
            affected_ticket_ids=str(affected_ticket_ids),
            root_cause=root_cause,
            business_impact=business_impact,
            status='active'
        )

        print(f"\n💾 Recording operational insight...")
        insight_id = self.ops_intel.add_insight(insight)
        print(f"   ✅ Insight #{insight_id} saved and embedded for future pattern matching")

        return insight_id

    def record_recommendation(
        self,
        insight_id: int,
        recommendation_type: str,
        title: str,
        description: str,
        estimated_effort: str,
        estimated_impact: str,
        priority: str,
        assigned_to: str = None,
        due_date: str = None
    ) -> int:
        """
        Step 3: Record recommendation.

        Args:
            insight_id: ID from record_insight()
            recommendation_type: training, process_change, staffing, tooling, knowledge_base, skill_routing, customer_communication
            title: Short title
            description: Detailed description
            estimated_effort: e.g., "2 weeks", "4 hours"
            estimated_impact: Expected improvement
            priority: critical, high, medium, low
            assigned_to: Person/team responsible
            due_date: YYYY-MM-DD format

        Returns:
            recommendation_id
        """

        rec = Recommendation(
            insight_id=insight_id,
            recommendation_type=recommendation_type,
            title=title,
            description=description,
            estimated_effort=estimated_effort,
            estimated_impact=estimated_impact,
            priority=priority,
            status='proposed',
            assigned_to=assigned_to or '',
            due_date=due_date or ''
        )

        rec_id = self.ops_intel.add_recommendation(rec)
        print(f"   💡 Recommendation #{rec_id} recorded")

        return rec_id

    def log_action(
        self,
        recommendation_id: int,
        action_type: str,
        action_date: str,
        performed_by: str,
        details: str,
        ticket_ids: List[int] = None,
        artifacts: Dict = None
    ) -> int:
        """
        Step 4: Log action taken.

        Args:
            recommendation_id: ID from record_recommendation()
            action_type: ticket_assignment, customer_communication, training_session, kb_article, process_update, tool_implementation
            action_date: YYYY-MM-DD format
            performed_by: Person who performed action
            details: Description of what was done
            ticket_ids: Optional list of affected tickets
            artifacts: Optional dict (e.g., {"attendance": 8, "quiz_score": 85})

        Returns:
            action_id
        """

        action = ActionTaken(
            recommendation_id=recommendation_id,
            action_type=action_type,
            action_date=action_date,
            performed_by=performed_by,
            details=details,
            ticket_ids=str(ticket_ids) if ticket_ids else '',
            artifacts=str(artifacts) if artifacts else ''
        )

        action_id = self.ops_intel.log_action(action)
        print(f"   ✅ Action #{action_id} logged")

        return action_id

    def track_outcome(
        self,
        recommendation_id: int,
        metric_type: str,
        baseline_value: float,
        current_value: float,
        target_value: float,
        measurement_period: str,
        sample_size: int,
        notes: str = ''
    ) -> int:
        """
        Step 5: Track outcome (30-60 days after action).

        Args:
            recommendation_id: ID from record_recommendation()
            metric_type: fcr_rate, escalation_rate, csat_score, resolution_time_avg, sla_compliance, client_complaints
            baseline_value: Value before intervention
            current_value: Value after intervention
            target_value: Original goal
            measurement_period: e.g., "30 days post-training"
            sample_size: Number of tickets/interactions measured
            notes: Additional context

        Returns:
            outcome_id
        """

        outcome = Outcome(
            recommendation_id=recommendation_id,
            measurement_date=datetime.now().isoformat(),
            metric_type=metric_type,
            baseline_value=baseline_value,
            current_value=current_value,
            target_value=target_value,
            measurement_period=measurement_period,
            sample_size=sample_size,
            notes=notes
        )

        outcome_id = self.ops_intel.track_outcome(outcome)

        # Calculate improvement
        improvement_pct = ((current_value - baseline_value) / baseline_value) * 100 if baseline_value > 0 else 0

        print(f"   📈 Outcome tracked: {metric_type}")
        print(f"      Baseline: {baseline_value} → Current: {current_value} ({improvement_pct:+.1f}% change)")

        return outcome_id

    def record_learning(
        self,
        insight_id: int,
        recommendation_id: int,
        learning_type: str,
        what_worked: str,
        what_didnt_work: str,
        why_analysis: str,
        confidence_before: float,
        confidence_after: float,
        would_recommend_again: bool,
        similar_situations: str,
        tags: List[str]
    ) -> int:
        """
        Step 6: Record learning after completion.

        Automatically embeds in ChromaDB for future retrieval.

        Args:
            insight_id: Original insight ID
            recommendation_id: Recommendation that was implemented
            learning_type: success, partial_success, failure, unexpected_outcome
            what_worked: What was effective
            what_didnt_work: What didn't work
            why_analysis: Root cause of success/failure
            confidence_before: 0-100 confidence before
            confidence_after: 0-100 confidence after
            would_recommend_again: Boolean
            similar_situations: When to apply this learning
            tags: List of tags (e.g., ["training", "escalation_reduction"])

        Returns:
            learning_id
        """

        learning = Learning(
            insight_id=insight_id,
            recommendation_id=recommendation_id,
            learning_type=learning_type,
            what_worked=what_worked,
            what_didnt_work=what_didnt_work,
            why_analysis=why_analysis,
            confidence_before=confidence_before,
            confidence_after=confidence_after,
            would_recommend_again=would_recommend_again,
            similar_situations=similar_situations,
            tags=str(tags)
        )

        print(f"\n🎓 Recording institutional learning...")
        learning_id = self.ops_intel.add_learning(learning)
        print(f"   ✅ Learning #{learning_id} saved and embedded for future reference")
        print(f"   📊 Confidence gain: {confidence_before}% → {confidence_after}% (+{confidence_after - confidence_before} points)")

        return learning_id

    def search_similar_learnings(self, query: str, top_k: int = 3) -> List[Dict]:
        """
        Search for relevant past learnings using semantic search.

        Use this when generating recommendations to reference what worked before.

        Args:
            query: Natural language query (e.g., "training effectiveness")
            top_k: Number of results

        Returns:
            List of similar learnings with scores
        """

        print(f"\n🔍 Searching institutional knowledge for '{query}'...")
        results = self.ops_intel.find_similar_learnings(query, top_k=top_k)

        if results:
            print(f"   ✅ Found {len(results)} relevant learnings:")
            for idx, learning in enumerate(results, 1):
                print(f"   {idx}. {learning['learning_type'].upper()} (Similarity: {learning['similarity_score']:.1%})")
                print(f"      What worked: {learning['what_worked'][:80]}...")
        else:
            print(f"   ℹ️  No similar learnings found")

        return results

    def get_dashboard_summary(self) -> Dict:
        """Get quick summary of operational intelligence"""
        return self.ops_intel.get_dashboard_summary()


# Convenience function for SDM Agent
def get_ops_intel_helper():
    """Factory function to get SDM Agent ops intelligence helper"""
    return SDMAgentOpsIntelHelper()


if __name__ == '__main__':
    # Demo usage
    helper = SDMAgentOpsIntelHelper()

    print("="*80)
    print("SDM AGENT OPERATIONS INTELLIGENCE INTEGRATION - DEMO")
    print("="*80)

    # Demo: Check for similar patterns
    result = helper.start_complaint_analysis(
        complaint_description="Azure authentication failures causing ticket escalations",
        affected_clients=["Client D"],
        affected_categories=["Azure", "Authentication"]
    )

    print(f"\n📊 Dashboard Summary:")
    summary = helper.get_dashboard_summary()
    for key, value in summary.items():
        print(f"   {key}: {value}")
