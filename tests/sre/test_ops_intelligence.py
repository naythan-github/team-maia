#!/usr/bin/env python3
"""
Test ServiceDesk Operations Intelligence Database

Creates sample data to validate system functionality
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from servicedesk_operations_intelligence import (
    ServiceDeskOpsIntelligence,
    OperationalInsight,
    Recommendation,
    ActionTaken,
    Outcome,
    Pattern,
    Learning
)

def create_sample_data():
    """Create sample operational intelligence data"""

    ops_intel = ServiceDeskOpsIntelligence()
    print("🧪 Creating sample operational intelligence data...\n")

    # Sample 1: Exchange Hybrid Escalation Pattern
    print("📌 Creating Insight 1: Exchange Hybrid Escalation Pattern")
    insight1 = OperationalInsight(
        insight_type='escalation_bottleneck',
        title='Exchange hybrid tickets have 70% escalation rate',
        description='Exchange hybrid tickets require excessive Microsoft support escalations due to L2 knowledge gap. Average 5.2 handoffs per ticket vs 1.8 baseline.',
        identified_date='2025-10-18',
        severity='high',
        affected_clients='["Client A", "Client B", "Client C"]',
        affected_categories='["Exchange", "M365"]',
        affected_ticket_ids='[12345, 12346, 12350, 12355]',
        root_cause='L2 team lacks Exchange hybrid troubleshooting training → excessive Microsoft escalations → 5.2 avg handoffs',
        business_impact='70% escalation rate (4.7x baseline), avg 18h resolution vs 6h target',
        status='active'
    )
    insight1_id = ops_intel.add_insight(insight1)

    # Recommendation for Insight 1
    print("💡 Creating Recommendation 1: Exchange Hybrid Training")
    rec1 = Recommendation(
        insight_id=insight1_id,
        recommendation_type='training',
        title='Exchange Hybrid Training for L2 Team',
        description='4-hour Microsoft Exchange hybrid troubleshooting training for L2 team (Rachel S., Tom K.). Topics: mailbox migration, hybrid authentication, mail flow, common issues.',
        estimated_effort='1 week to schedule + deliver',
        estimated_impact='Reduce Exchange escalation rate from 70% to 30%, improve resolution time from 18h to 8h',
        priority='high',
        status='completed',
        assigned_to='Training Coordinator',
        due_date='2025-10-25'
    )
    rec1_id = ops_intel.add_recommendation(rec1)

    # Action for Recommendation 1
    print("✅ Logging Action 1: Training Session Delivered")
    action1 = ActionTaken(
        recommendation_id=rec1_id,
        action_type='training_session',
        action_date='2025-10-20',
        performed_by='Training Coordinator',
        details='Delivered 4-hour Exchange Hybrid troubleshooting training. Topics: mailbox migration, hybrid authentication, mail flow troubleshooting, common issues.',
        artifacts='{"attendance": 8, "materials_url": "https://confluence/training/exchange-hybrid", "quiz_avg_score": 85}'
    )
    ops_intel.log_action(action1)

    # Outcome for Recommendation 1
    print("📈 Tracking Outcome 1: Escalation Rate Improvement")
    outcome1 = Outcome(
        recommendation_id=rec1_id,
        measurement_date='2025-11-20',
        metric_type='escalation_rate',
        baseline_value=70.0,
        current_value=28.0,
        target_value=30.0,
        measurement_period='30 days post-training',
        sample_size=45,
        notes='Exceeded target! Exchange hybrid escalation rate dropped from 70% to 28% (45 tickets measured). Training highly effective.'
    )
    ops_intel.track_outcome(outcome1)

    # Learning from Recommendation 1
    print("🎓 Recording Learning 1: Training Effectiveness")
    learning1 = Learning(
        insight_id=insight1_id,
        recommendation_id=rec1_id,
        learning_type='success',
        what_worked='4-hour focused training on Exchange hybrid troubleshooting with hands-on labs and real ticket examples',
        what_didnt_work='N/A - training exceeded expectations',
        why_analysis='Hands-on approach + real ticket examples made training immediately applicable. Team members could apply learnings same day.',
        confidence_before=75.0,
        confidence_after=95.0,
        would_recommend_again=True,
        similar_situations='Any category with >50% escalation rate due to knowledge gap. Hands-on training > theory for technical skills.',
        tags='["training_effectiveness", "exchange", "escalation_reduction", "hands_on_learning"]'
    )
    ops_intel.add_learning(learning1)

    # Pattern for Exchange Hybrid
    print("🔄 Adding Pattern 1: Exchange Hybrid Escalation Hotspot")
    pattern1 = Pattern(
        pattern_type='escalation_hotspot',
        pattern_description='Exchange hybrid tickets consistently escalate to Microsoft support',
        first_observed='2025-07-15',
        last_observed='2025-10-18',
        frequency='Weekly',
        occurrence_count=15,
        related_insights=f'[{insight1_id}]',
        related_tickets='[12345, 12346, 12350, 12355]',
        trigger_conditions='Category=Exchange AND Description contains "hybrid"',
        status='resolved'
    )
    ops_intel.add_pattern(pattern1)

    print("\n" + "="*80)

    # Sample 2: Azure Ticket Assignment Issue
    print("\n📌 Creating Insight 2: Azure Tickets Slow Due to Skills Gap")
    insight2 = OperationalInsight(
        insight_type='skill_gap',
        title='Azure tickets have 50% escalation rate - skills gap identified',
        description='8 tickets from Acme Corp, 4 escalated (50% rate vs 15% baseline). All 4 escalations required Azure expertise.',
        identified_date='2025-10-18',
        severity='high',
        affected_clients='["Acme Corp"]',
        affected_categories='["Azure"]',
        affected_ticket_ids='[12401, 12402, 12403, 12404, 12405, 12406, 12407, 12408]',
        root_cause='L2 team lacks Azure certification → all Azure issues escalate to L3 Sarah M.',
        business_impact='$180K annual contract at risk, 2 tickets breached SLA (8h commitment)',
        status='active'
    )
    insight2_id = ops_intel.add_insight(insight2)

    # Immediate action recommendation
    print("💡 Creating Recommendation 2: Immediate Ticket Assignment")
    rec2 = Recommendation(
        insight_id=insight2_id,
        recommendation_type='staffing',
        title='Assign all open Acme tickets to Azure specialist Sarah M.',
        description='Immediate assignment of 2 open Acme Corp Azure tickets to Sarah M. to prevent SLA breach',
        estimated_effort='30 minutes',
        estimated_impact='Prevent SLA breach, restore 4-hour resolution commitment',
        priority='critical',
        status='completed',
        assigned_to='Service Desk Manager',
        due_date='2025-10-18'
    )
    rec2_id = ops_intel.add_recommendation(rec2)

    # Long-term training recommendation
    print("💡 Creating Recommendation 3: Azure Training for L2")
    rec3 = Recommendation(
        insight_id=insight2_id,
        recommendation_type='training',
        title='Azure fundamentals training for 2 L2 techs',
        description='Train Rachel S. and Tom K. on Azure fundamentals (2 weeks). Topics: Azure AD, VMs, networking basics.',
        estimated_effort='2 weeks',
        estimated_impact='Reduce Azure escalation rate from 50% to 20%',
        priority='high',
        status='in_progress',
        assigned_to='Training Coordinator',
        due_date='2025-11-01'
    )
    rec3_id = ops_intel.add_recommendation(rec3)

    # Action for immediate assignment
    print("✅ Logging Action 2: Tickets Reassigned")
    action2 = ActionTaken(
        recommendation_id=rec2_id,
        action_type='ticket_assignment',
        action_date='2025-10-18',
        performed_by='Service Desk Manager',
        details='Reassigned tickets CRM-789 and CRM-791 to Sarah M. (Azure specialist). Added high-priority flag.',
        ticket_ids='[12407, 12408]',
        artifacts='{"tickets_reassigned": 2, "new_assignee": "Sarah M.", "priority_updated": true}'
    )
    ops_intel.log_action(action2)

    print("\n" + "="*80)
    print("\n✅ Sample data created successfully!\n")

    # Show dashboard
    print("📊 Dashboard Summary:")
    summary = ops_intel.get_dashboard_summary()
    for key, value in summary.items():
        print(f"   {key}: {value}")

    print("\n🔍 Testing search functionality:")
    search_results = ops_intel.search('Azure')
    print(f"   Search 'Azure': {len(search_results['insights'])} insights, {len(search_results['recommendations'])} recommendations")

    search_results2 = ops_intel.search('Exchange')
    print(f"   Search 'Exchange': {len(search_results2['insights'])} insights, {len(search_results2['patterns'])} patterns")

    print("\n✅ All tests passed! Database operational.\n")


if __name__ == '__main__':
    create_sample_data()
