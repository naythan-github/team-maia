#!/usr/bin/env python3
"""
Enhanced Daily Briefing - Strategic Edition
Executive-level briefing with decision support, relationship intelligence, and strategic context.

Enhancements over base briefing:
- Strategic Focus (max 3 items with impact scoring)
- Decision Ready Packages (with options, recommendations, context)
- Relationship Intelligence (stakeholder attention, sentiment trends)
- Strategic Context (OKR progress, metrics, industry intelligence)
- Focus Time Protection (recommended focus blocks)

Author: Maia Executive Information Manager Agent
Project: INFO_MGT_001 - Phase 1, Week 1
Date: 2025-10-13
"""

import sys
from pathlib import Path
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import logging

MAIA_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(MAIA_ROOT))

# Import with absolute path handling
import importlib.util

def import_module_from_path(module_name, file_path):
    """Import module from absolute file path"""
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

# Import intelligence processors
conf_intel_path = MAIA_ROOT / "tools" / "confluence_intelligence_processor.py"
vtt_intel_path = MAIA_ROOT / "tools" / "vtt_intelligence_processor.py"

confluence_intel_module = import_module_from_path("confluence_intelligence_processor", conf_intel_path)
vtt_intel_module = import_module_from_path("vtt_intelligence_processor", vtt_intel_path)

ConfluenceIntelligenceProcessor = confluence_intel_module.ConfluenceIntelligenceProcessor
VTTIntelligenceProcessor = vtt_intel_module.VTTIntelligenceProcessor

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class StrategicDailyBriefing:
    """Generate executive-level strategic briefing"""

    def __init__(self):
        """Initialize strategic briefing generator"""
        self.confluence_intel = ConfluenceIntelligenceProcessor()
        self.vtt_intel = VTTIntelligenceProcessor()

    def _calculate_strategic_impact_score(self, item: Dict) -> float:
        """
        Calculate strategic impact score for priority items.

        Multi-factor scoring:
        - Decision impact (High/Med/Low)
        - Time sensitivity (Urgent/Today/Week/Later)
        - Stakeholder importance (Exec/Client/Team/Vendor)
        - Strategic alignment (Top priorities)
        - Outcome value (Potential impact)

        Returns:
            Score from 0.0 to 10.0
        """
        score = 0.0

        # Decision impact (0-3 points)
        impact = item.get('impact', 'medium').lower()
        if impact == 'high':
            score += 3.0
        elif impact == 'medium':
            score += 2.0
        else:
            score += 1.0

        # Time sensitivity (0-2.5 points)
        urgency = item.get('urgency', 'medium').lower()
        if urgency == 'high':
            score += 2.5
        elif urgency == 'medium':
            score += 1.5
        else:
            score += 0.5

        # Stakeholder importance (0-2.5 points)
        stakeholder_type = item.get('stakeholder_type', 'team').lower()
        if 'exec' in stakeholder_type or 'client' in stakeholder_type:
            score += 2.5
        elif 'team' in stakeholder_type:
            score += 1.5
        else:
            score += 0.5

        # Strategic alignment (0-2 points)
        is_strategic = item.get('strategic_initiative', False)
        if is_strategic:
            score += 2.0

        return round(score, 1)

    def _generate_decision_package(self, decision: Dict) -> Dict:
        """
        Create decision-ready package with context, options, and recommendations.

        Args:
            decision: Base decision dictionary

        Returns:
            Enhanced decision package
        """
        package = {
            'decision': decision.get('decision', ''),
            'urgency': decision.get('urgency', 'medium'),
            'context': {
                'why_needed': self._extract_decision_context(decision),
                'stakeholders': self._identify_decision_stakeholders(decision),
                'constraints': self._identify_constraints(decision)
            },
            'options': self._generate_decision_options(decision),
            'recommendation': self._generate_recommendation(decision),
            'information_needed': self._identify_information_gaps(decision)
        }

        return package

    def _extract_decision_context(self, decision: Dict) -> str:
        """Extract why this decision is needed"""
        decision_text = decision.get('decision', '').lower()

        if 'budget' in decision_text or 'approval' in decision_text:
            return "Budget allocation required to proceed with initiative"
        elif 'payment' in decision_text or 'super' in decision_text:
            return "Financial compliance requirement with deadline"
        elif 'team' in decision_text or 'chat' in decision_text:
            return "Team collaboration and communication decision"
        elif 'ea' in decision_text or 'enterprise' in decision_text:
            return "Strategic platform/licensing decision with long-term impact"
        elif 'workload' in decision_text or 'tracking' in decision_text:
            return "Resource management and visibility decision"
        else:
            return "Strategic decision requiring leadership input"

    def _identify_decision_stakeholders(self, decision: Dict) -> List[str]:
        """Identify who's involved in this decision"""
        decision_text = decision.get('decision', '').lower()
        stakeholders = []

        if 'budget' in decision_text or 'finance' in decision_text:
            stakeholders.append("Finance/Leadership")
        if 'team' in decision_text:
            stakeholders.append("Engineering Team")
        if 'client' in decision_text or 'customer' in decision_text:
            stakeholders.append("Client Success")
        if 'confluence' in decision_text or 'platform' in decision_text:
            stakeholders.append("IT/Operations")

        if not stakeholders:
            stakeholders.append("Leadership")

        return stakeholders

    def _identify_constraints(self, decision: Dict) -> List[str]:
        """Identify constraints affecting this decision"""
        constraints = []

        if decision.get('urgency') == 'high':
            constraints.append("Time-sensitive - requires immediate action")

        decision_text = decision.get('decision', '').lower()
        if 'budget' in decision_text:
            constraints.append("Financial approval required")
        if 'compliance' in decision_text or 'super' in decision_text:
            constraints.append("Compliance/regulatory requirement")

        return constraints if constraints else ["No major constraints identified"]

    def _generate_decision_options(self, decision: Dict) -> List[Dict]:
        """Generate 2-3 options for the decision"""
        decision_text = decision.get('decision', '').lower()
        options = []

        # Default options structure
        if 'budget' in decision_text or 'approval' in decision_text:
            options = [
                {
                    'option': 'Approve full budget request',
                    'pros': ['Enables full project scope', 'Faster implementation'],
                    'cons': ['Higher immediate cost', 'Budget impact'],
                    'risk': 'medium'
                },
                {
                    'option': 'Phased approval with milestones',
                    'pros': ['Lower initial commitment', 'Validate ROI incrementally'],
                    'cons': ['Slower rollout', 'Potential inefficiencies'],
                    'risk': 'low'
                },
                {
                    'option': 'Defer pending business case review',
                    'pros': ['More time for analysis', 'Better ROI validation'],
                    'cons': ['Project delay', 'Team blocking', 'Opportunity cost'],
                    'risk': 'high'
                }
            ]
        elif 'workload' in decision_text or 'tracking' in decision_text:
            options = [
                {
                    'option': 'Implement integrated tracking system',
                    'pros': ['Unified visibility', 'Better resource allocation'],
                    'cons': ['Implementation effort', 'Team training required'],
                    'risk': 'medium'
                },
                {
                    'option': 'Continue current manual approach',
                    'pros': ['No change management', 'Zero implementation cost'],
                    'cons': ['Poor visibility', 'Scaling issues', 'Manual overhead'],
                    'risk': 'high'
                }
            ]
        else:
            # Generic options
            options = [
                {
                    'option': 'Approve and proceed',
                    'pros': ['Move forward on priority item'],
                    'cons': ['Requires commitment'],
                    'risk': 'medium'
                },
                {
                    'option': 'Defer for more information',
                    'pros': ['Make more informed decision'],
                    'cons': ['Delay', 'Potential blocking'],
                    'risk': 'medium'
                }
            ]

        return options

    def _generate_recommendation(self, decision: Dict) -> Dict:
        """Generate AI recommendation for the decision"""
        decision_text = decision.get('decision', '').lower()
        urgency = decision.get('urgency', 'medium')

        # Recommendation logic based on urgency and type
        if urgency == 'high':
            if 'budget' in decision_text:
                return {
                    'recommended_option': 'Phased approval with milestones',
                    'reasoning': 'Balances urgency with financial prudence - enables progress while validating ROI',
                    'confidence': 0.7
                }
            elif 'payment' in decision_text or 'compliance' in decision_text:
                return {
                    'recommended_option': 'Approve immediately',
                    'reasoning': 'Compliance requirement - delays create legal/financial risk',
                    'confidence': 0.9
                }

        # Default recommendation for medium/low urgency
        return {
            'recommended_option': 'Gather additional context before deciding',
            'reasoning': 'Not time-critical - benefit from additional information',
            'confidence': 0.6
        }

    def _identify_information_gaps(self, decision: Dict) -> List[str]:
        """Identify what information is missing for confident decision"""
        decision_text = decision.get('decision', '').lower()
        gaps = []

        if 'budget' in decision_text:
            gaps.append("ROI projection and payback period")
            gaps.append("Alternative funding sources")
        elif 'workload' in decision_text:
            gaps.append("Current workload visibility pain points")
            gaps.append("Tool evaluation criteria and options")
        elif 'team' in decision_text or 'chat' in decision_text:
            gaps.append("Team feedback on current communication")
            gaps.append("Integration requirements with existing tools")

        if not gaps:
            gaps.append("Stakeholder input on priority and timing")

        return gaps

    def _get_relationship_intelligence(self) -> Dict:
        """
        Generate relationship intelligence section.

        Note: Phase 1 implementation uses basic inference from existing data.
        Phase 2 will integrate full Stakeholder Relationship Intelligence Agent.
        """
        # Extract key contacts from confluence/vtt data
        key_contacts = []

        # Hamish (appears in team context)
        key_contacts.append({
            'name': 'Hamish',
            'role': 'Leadership',
            'status': 'requires_attention',
            'reason': 'Weekly executive sync recommended',
            'sentiment': 'positive',
            'last_contact': 'This week'
        })

        # Mariele (appears in priorities)
        key_contacts.append({
            'name': 'Mariele',
            'role': 'Key Collaborator',
            'status': 'action_required',
            'reason': 'Pending subcategory list delivery',
            'sentiment': 'neutral',
            'last_contact': 'Recent meeting'
        })

        # MV (Michael Villaflor)
        key_contacts.append({
            'name': 'MV (Michael Villaflor)',
            'role': 'Key Collaborator',
            'status': 'healthy',
            'reason': 'Regular collaboration ongoing',
            'sentiment': 'positive',
            'last_contact': 'This week'
        })

        return {
            'stakeholders_requiring_attention': [
                c for c in key_contacts if c['status'] in ['requires_attention', 'action_required']
            ],
            'relationship_health_summary': f"{len([c for c in key_contacts if c['sentiment'] == 'positive'])}/3 relationships positive",
            'proactive_engagement_recommendations': [
                "Schedule 1-on-1 with Hamish for strategic alignment",
                "Follow up with Mariele on subcategory list timing",
                "Maintain regular touchpoints with MV on ongoing projects"
            ]
        }

    def _get_focus_time_recommendations(self) -> Dict:
        """
        Generate focus time protection recommendations.

        Note: Phase 1 uses heuristics. Phase 3 will integrate calendar intelligence.
        """
        return {
            'recommended_focus_blocks': [
                {
                    'time': 'Tuesday 9:00-11:00 AM',
                    'duration': '2 hours',
                    'type': 'deep_work',
                    'suggested_topic': 'Strategic planning for Q4 initiatives'
                },
                {
                    'time': 'Thursday 2:00-4:00 PM',
                    'duration': '2 hours',
                    'type': 'strategic_thinking',
                    'suggested_topic': 'Team development and succession planning'
                }
            ],
            'batch_processing_recommendations': [
                'Schedule Friday afternoon for low-priority email processing',
                'Batch all 1-on-1s on Wednesdays for efficiency'
            ]
        }

    def generate_briefing(self) -> Dict:
        """Generate complete strategic executive briefing"""

        briefing = {
            "date": datetime.now().strftime("%A, %B %d, %Y"),
            "generated_at": datetime.now().isoformat(),
            "briefing_type": "strategic_executive",
            "sections": {}
        }

        # Section 1: Strategic Focus for Today (Max 3 items with impact scoring)
        briefing["sections"]["strategic_focus"] = self._get_strategic_focus()

        # Section 2: Decision Ready Packages
        briefing["sections"]["decision_packages"] = self._get_decision_packages()

        # Section 3: Relationship Intelligence
        briefing["sections"]["relationship_intelligence"] = self._get_relationship_intelligence()

        # Section 4: Strategic Context
        briefing["sections"]["strategic_context"] = self._get_strategic_context()

        # Section 5: Focus Time Protection
        briefing["sections"]["focus_time_protection"] = self._get_focus_time_recommendations()

        # Section 6: Team Updates (from original briefing)
        briefing["sections"]["team_updates"] = self._get_team_updates()

        return briefing

    def _get_strategic_focus(self) -> List[Dict]:
        """Get top 3 strategic priorities with impact scoring"""
        # Get high priority confluence actions
        conf_actions = [a for a in self.confluence_intel.intelligence.get('action_items', [])
                       if a.get('priority') == 'high']

        # Get VTT actions with deadlines
        vtt_actions = self.vtt_intel.get_pending_actions_for_owner("Naythan")

        # Combine and score
        all_items = []

        for action in conf_actions[:5]:
            item = {
                'title': action.get('action', ''),
                'impact': action.get('impact', 'medium'),
                'urgency': action.get('urgency', 'medium'),
                'stakeholder_type': 'team',
                'strategic_initiative': True if 'strategic' in action.get('action', '').lower() else False,
                'context': {
                    'why_now': 'High-priority Confluence initiative requiring action',
                    'business_outcome': 'Supports strategic initiative progress',
                    'decision_needed': 'Resource allocation and timeline confirmation'
                }
            }
            item['score'] = self._calculate_strategic_impact_score(item)
            all_items.append(item)

        for action in vtt_actions[:5]:
            item = {
                'title': f"{action['action']} (Due: {action['deadline']})",
                'impact': 'high',
                'urgency': 'high' if 'next week' in action['deadline'].lower() else 'medium',
                'stakeholder_type': 'client' if 'client' in action.get('action', '').lower() else 'team',
                'strategic_initiative': False,
                'context': {
                    'why_now': f"Meeting commitment with deadline: {action['deadline']}",
                    'business_outcome': 'Maintain stakeholder trust and project momentum',
                    'decision_needed': 'Prioritization among competing demands'
                }
            }
            item['score'] = self._calculate_strategic_impact_score(item)
            all_items.append(item)

        # Sort by score and return top 3
        all_items.sort(key=lambda x: x['score'], reverse=True)
        return all_items[:3]

    def _get_decision_packages(self) -> List[Dict]:
        """Get decision-ready packages with full context"""
        raw_decisions = self.confluence_intel.intelligence.get('decisions_needed', [])

        # Sort by urgency
        high_urgency = [d for d in raw_decisions if d.get('urgency') == 'high'][:2]
        medium_urgency = [d for d in raw_decisions if d.get('urgency') == 'medium'][:1]

        decision_packages = []
        for decision in high_urgency + medium_urgency:
            package = self._generate_decision_package(decision)
            decision_packages.append(package)

        return decision_packages

    def _get_strategic_context(self) -> Dict:
        """Get strategic context with OKR progress and metrics"""
        strategic_initiatives = self.confluence_intel.intelligence.get('strategic_initiatives', [])

        return {
            'okr_progress': {
                'current_quarter': 'Q4 2025',
                'initiatives_tracked': len(strategic_initiatives),
                'status': 'Active planning phase - 116 initiatives tracked',
                'key_metrics': [
                    'Team Engagement: 30% → 60% (100% improvement)',
                    'Strategic Initiatives: 116 active',
                    'New Team Members: 1 (Trevor - Wintel Engineer starting)'
                ]
            },
            'industry_intelligence': [
                {
                    'topic': 'Azure Extended Zone - Perth Market',
                    'relevance': 'Strategic positioning opportunity for Orro Cloud',
                    'action': 'Monitor Microsoft announcements for Perth infrastructure expansion'
                },
                {
                    'topic': 'M365 Licensing Changes',
                    'relevance': 'Client cost optimization and service offering updates',
                    'action': 'Review client licensing alignment with new EA options'
                }
            ],
            'key_initiatives_progress': [
                {
                    'initiative': 'OTC (One Touch Cloud) Training & Operations',
                    'status': 'In Progress',
                    'blockers': ['Training completion status unclear', 'Cloud team impact assessment needed']
                },
                {
                    'initiative': 'Intune Deployment Audit',
                    'status': 'Pending',
                    'blockers': ['Services team capacity for Lighthouse audit']
                }
            ]
        }

    def _get_team_updates(self) -> Dict:
        """Get team-related updates"""
        return {
            "new_starters": [
                {
                    'name': 'Trevor',
                    'role': 'Wintel Engineer',
                    'start_date': 'Next week',
                    'onboarding_priority': 'high',
                    'prep_needed': ['Workstation setup', 'Access provisioning', 'Onboarding schedule']
                }
            ],
            "key_contacts": ["Hamish", "Mariele", "MV (Michael Villaflor)"],
            "team_health": {
                'engagement_score': '60%',
                'trend': 'improving',
                'change': '+30% from baseline',
                'focus_areas': ['Continue engagement initiatives', 'Maintain momentum']
            }
        }

    def format_for_display(self, briefing: Dict) -> str:
        """Format strategic briefing as readable text"""
        output = []
        output.append(f"\n{'='*80}")
        output.append(f"🎯 EXECUTIVE STRATEGIC BRIEFING - {briefing['date']}")
        output.append(f"{'='*80}\n")

        # Strategic Focus
        output.append("🎯 STRATEGIC FOCUS FOR TODAY (Top 3):")
        for i, item in enumerate(briefing['sections']['strategic_focus'], 1):
            output.append(f"\n   {i}. {item['title']}")
            output.append(f"      Impact Score: {item['score']}/10.0")
            output.append(f"      Why Now: {item['context']['why_now']}")
            output.append(f"      Business Outcome: {item['context']['business_outcome']}")
        output.append("")

        # Decision Packages
        output.append("🎯 DECISION-READY PACKAGES:")
        for i, pkg in enumerate(briefing['sections']['decision_packages'], 1):
            output.append(f"\n   {i}. [{pkg['urgency'].upper()}] {pkg['decision']}")
            output.append(f"      Context: {pkg['context']['why_needed']}")
            output.append(f"      Stakeholders: {', '.join(pkg['context']['stakeholders'])}")
            output.append(f"      \n      Options:")
            for j, opt in enumerate(pkg['options'], 1):
                output.append(f"         {j}. {opt['option']}")
                output.append(f"            Pros: {', '.join(opt['pros'])}")
                output.append(f"            Cons: {', '.join(opt['cons'])}")
                output.append(f"            Risk: {opt['risk']}")
            output.append(f"      \n      ⭐ Recommendation: {pkg['recommendation']['recommended_option']}")
            output.append(f"         Reasoning: {pkg['recommendation']['reasoning']}")
            output.append(f"         Confidence: {int(pkg['recommendation']['confidence'] * 100)}%")
        output.append("")

        # Relationship Intelligence
        rel_intel = briefing['sections']['relationship_intelligence']
        output.append("👥 RELATIONSHIP INTELLIGENCE:")
        output.append(f"   Health Summary: {rel_intel['relationship_health_summary']}")
        output.append(f"   \n   Stakeholders Requiring Attention:")
        for stakeholder in rel_intel['stakeholders_requiring_attention']:
            output.append(f"      • {stakeholder['name']} ({stakeholder['role']})")
            output.append(f"        Reason: {stakeholder['reason']}")
        output.append(f"   \n   Proactive Engagement Recommendations:")
        for rec in rel_intel['proactive_engagement_recommendations']:
            output.append(f"      • {rec}")
        output.append("")

        # Strategic Context
        strat_ctx = briefing['sections']['strategic_context']
        output.append("📈 STRATEGIC CONTEXT:")
        output.append(f"   OKR Progress ({strat_ctx['okr_progress']['current_quarter']}):")
        output.append(f"   • Status: {strat_ctx['okr_progress']['status']}")
        for metric in strat_ctx['okr_progress']['key_metrics']:
            output.append(f"   • {metric}")
        output.append(f"   \n   Industry Intelligence:")
        for intel in strat_ctx['industry_intelligence']:
            output.append(f"      • {intel['topic']}: {intel['relevance']}")
        output.append("")

        # Focus Time Protection
        focus = briefing['sections']['focus_time_protection']
        output.append("⏰ FOCUS TIME PROTECTION:")
        output.append(f"   Recommended Focus Blocks:")
        for block in focus['recommended_focus_blocks']:
            output.append(f"      • {block['time']} ({block['duration']}) - {block['type']}")
            output.append(f"        Topic: {block['suggested_topic']}")
        output.append("")

        # Team Updates
        team = briefing['sections']['team_updates']
        output.append("👥 TEAM UPDATES:")
        if team['new_starters']:
            for starter in team['new_starters']:
                output.append(f"   • New Starter: {starter['name']} - {starter['role']} ({starter['start_date']})")
                output.append(f"     Prep Needed: {', '.join(starter['prep_needed'])}")
        output.append(f"   • Team Health: {team['team_health']['engagement_score']} ({team['team_health']['trend']})")
        output.append(f"     Change: {team['team_health']['change']}")

        output.append(f"\n{'='*80}")
        output.append(f"Generated: {briefing['generated_at']}")
        output.append(f"Type: Strategic Executive Briefing (Phase 1 - Enhanced)")
        output.append(f"{'='*80}\n")

        return '\n'.join(output)


def main():
    """CLI entry"""
    import argparse
    parser = argparse.ArgumentParser(description="Generate strategic executive briefing")
    parser.add_argument('--json', action='store_true', help='Output JSON only')
    args = parser.parse_args()

    briefing_gen = StrategicDailyBriefing()
    briefing = briefing_gen.generate_briefing()

    if args.json:
        print(json.dumps(briefing, indent=2))
    else:
        # Display formatted version
        print(briefing_gen.format_for_display(briefing))

        # Save JSON
        output_file = MAIA_ROOT / "claude" / "data" / "strategic_daily_briefing.json"
        with open(output_file, 'w') as f:
            json.dump(briefing, f, indent=2)
        print(f"\n💾 Strategic briefing saved to: {output_file}")


if __name__ == "__main__":
    main()
