#!/usr/bin/env python3
"""
Enhanced Daily Briefing with Executive Intelligence
Integrates Confluence and VTT intelligence for comprehensive morning briefing

Author: Maia Personal Assistant Agent
Phase: 86.4 - Executive Command Center
Date: 2025-10-03
"""

import sys
from pathlib import Path
import json
from datetime import datetime
from typing import Dict, List

MAIA_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(MAIA_ROOT))

from claude.tools.confluence_intelligence_processor import ConfluenceIntelligenceProcessor
from claude.tools.vtt_intelligence_processor import VTTIntelligenceProcessor


class EnhancedDailyBriefing:
    """Generate executive briefing with full intelligence integration"""

    def __init__(self):
        """Initialize briefing generator"""
        self.confluence_intel = ConfluenceIntelligenceProcessor()
        self.vtt_intel = VTTIntelligenceProcessor()

    def generate_briefing(self) -> Dict:
        """Generate complete executive briefing"""

        briefing = {
            "date": datetime.now().strftime("%A, %B %d, %Y"),
            "generated_at": datetime.now().isoformat(),
            "sections": {}
        }

        # Section 1: Top Priorities Today
        briefing["sections"]["priorities"] = self._get_top_priorities()

        # Section 2: Decisions Needed
        briefing["sections"]["decisions"] = self._get_decisions_needed()

        # Section 3: Open Questions (Top 5)
        briefing["sections"]["questions"] = self._get_top_questions()

        # Section 4: Strategic Status
        briefing["sections"]["strategic"] = self._get_strategic_status()

        # Section 5: Team Updates
        briefing["sections"]["team"] = self._get_team_updates()

        # Section 6: Action Items from Meetings
        briefing["sections"]["meeting_actions"] = self._get_meeting_actions()

        return briefing

    def _get_top_priorities(self) -> List[str]:
        """Get top 5 priorities for today"""
        priorities = []

        # High priority confluence actions
        conf_actions = [a for a in self.confluence_intel.intelligence.get('action_items', [])
                       if a.get('priority') == 'high'][:3]
        priorities.extend([f"📋 {a['action']}" for a in conf_actions])

        # VTT actions with deadlines
        vtt_actions = self.vtt_intel.get_pending_actions_for_owner("Naythan")[:2]
        priorities.extend([f"📅 {a['action']} (Due: {a['deadline']})" for a in vtt_actions])

        return priorities[:5]

    def _get_decisions_needed(self) -> List[Dict]:
        """Get decisions requiring attention"""
        decisions = self.confluence_intel.intelligence.get('decisions_needed', [])

        # Sort by urgency
        high_urgency = [d for d in decisions if d.get('urgency') == 'high'][:3]
        medium_urgency = [d for d in decisions if d.get('urgency') == 'medium'][:2]

        return high_urgency + medium_urgency

    def _get_top_questions(self) -> List[str]:
        """Get top unanswered questions"""
        questions = self.confluence_intel.intelligence.get('questions', [])
        return [q['question'] for q in questions[:5]]

    def _get_strategic_status(self) -> Dict:
        """Get strategic initiatives status"""
        strategic = self.confluence_intel.intelligence.get('strategic_initiatives', [])

        return {
            "total_initiatives": len(strategic),
            "key_initiatives": [s['initiative'] for s in strategic[:3]],
            "status": "Active planning phase"
        }

    def _get_team_updates(self) -> Dict:
        """Get team-related updates"""
        return {
            "new_starters": ["Trevor - Wintel Engineer (starting next week)"],
            "key_contacts": ["Hamish", "Mariele", "MV (Michael Villaflor)"],
            "team_health": "Engagement improving: 30% → 60%"
        }

    def _get_meeting_actions(self) -> List[str]:
        """Get action items from recent meetings"""
        vtt_actions = self.vtt_intel.get_pending_actions_for_owner("Naythan")
        return [f"{a['action']} (from meeting)" for a in vtt_actions[:5]]

    def format_for_display(self, briefing: Dict) -> str:
        """Format briefing as readable text"""
        output = []
        output.append(f"\n{'='*70}")
        output.append(f"🎯 EXECUTIVE BRIEFING - {briefing['date']}")
        output.append(f"{'='*70}\n")

        # Priorities
        output.append("📌 TOP PRIORITIES TODAY:")
        for i, priority in enumerate(briefing['sections']['priorities'], 1):
            output.append(f"   {i}. {priority}")
        output.append("")

        # Decisions
        output.append("🎯 DECISIONS NEEDED:")
        for i, decision in enumerate(briefing['sections']['decisions'], 1):
            urgency = decision.get('urgency', 'medium').upper()
            output.append(f"   {i}. [{urgency}] {decision['decision']}")
        output.append("")

        # Questions
        output.append("❓ TOP OPEN QUESTIONS:")
        for i, question in enumerate(briefing['sections']['questions'], 1):
            output.append(f"   {i}. {question}")
        output.append("")

        # Strategic
        strategic = briefing['sections']['strategic']
        output.append("📈 STRATEGIC STATUS:")
        output.append(f"   • Total Initiatives: {strategic['total_initiatives']}")
        output.append(f"   • Status: {strategic['status']}")
        output.append("   Key Initiatives:")
        for init in strategic['key_initiatives']:
            output.append(f"     - {init}")
        output.append("")

        # Team
        team = briefing['sections']['team']
        output.append("👥 TEAM UPDATES:")
        output.append(f"   • New Starters: {', '.join(team['new_starters'])}")
        output.append(f"   • Team Health: {team['team_health']}")
        output.append("")

        # Meeting Actions
        output.append("📋 ACTION ITEMS FROM MEETINGS:")
        for i, action in enumerate(briefing['sections']['meeting_actions'], 1):
            output.append(f"   {i}. {action}")

        output.append(f"\n{'='*70}")
        output.append(f"Generated: {briefing['generated_at']}")
        output.append(f"{'='*70}\n")

        return '\n'.join(output)


def main():
    """CLI entry"""
    briefing_gen = EnhancedDailyBriefing()
    briefing = briefing_gen.generate_briefing()

    # Display
    print(briefing_gen.format_for_display(briefing))

    # Save
    output_file = MAIA_ROOT / "claude" / "data" / "enhanced_daily_briefing.json"
    with open(output_file, 'w') as f:
        json.dump(briefing, f, indent=2)

    print(f"\n💾 Briefing saved to: {output_file}")


if __name__ == "__main__":
    main()
