#!/usr/bin/env python3
"""
Trello Card Q&A System
Answer questions about Trello cards using source intelligence

Author: Maia Personal Assistant Agent
Phase: 88 - Personal Assistant Automation Expansion
Date: 2025-10-03
"""

import sys
from pathlib import Path
import json
from typing import Dict, List, Optional

MAIA_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(MAIA_ROOT))

from claude.tools.trello_fast import TrelloFast
from claude.tools.vtt_intelligence_processor import VTTIntelligenceProcessor


class TrelloCardQA:
    """Answer questions about Trello cards using source intelligence"""

    def __init__(self):
        """Initialize Q&A system"""
        self.trello = TrelloFast()
        self.vtt_intel = VTTIntelligenceProcessor()

    def get_card_context(self, card_name: str) -> Dict:
        """Get full context for a card"""
        # Find matching action in intelligence database
        for action in self.vtt_intel.intelligence["action_items"]:
            if card_name.lower() in action["action"].lower():
                source_file = action.get("source_file")
                if source_file and Path(source_file).exists():
                    # Read source summary
                    with open(source_file) as f:
                        summary_content = f.read()

                    return {
                        "card_action": action,
                        "source_file": source_file,
                        "meeting_name": Path(source_file).stem.replace('_summary', ''),
                        "full_summary": summary_content,
                        "related_decisions": self._get_related_decisions(source_file),
                        "related_actions": self._get_related_actions(source_file, action["action"])
                    }

        return {"error": "Card not found in intelligence database"}

    def _get_related_decisions(self, source_file: str) -> List[Dict]:
        """Get decisions from same meeting"""
        return [
            d for d in self.vtt_intel.intelligence["decisions"]
            if d.get("source_file") == source_file
        ]

    def _get_related_actions(self, source_file: str, exclude_action: str) -> List[Dict]:
        """Get other actions from same meeting"""
        return [
            a for a in self.vtt_intel.intelligence["action_items"]
            if a.get("source_file") == source_file and a["action"] != exclude_action
        ]

    def answer_question(self, card_name: str, question: str) -> str:
        """Answer a question about a card"""
        context = self.get_card_context(card_name)

        if "error" in context:
            return f"❌ {context['error']}"

        # Generate answer based on question type
        question_lower = question.lower()

        if "context" in question_lower or "background" in question_lower:
            return self._format_context_answer(context)
        elif "decision" in question_lower:
            return self._format_decisions_answer(context)
        elif "action" in question_lower or "task" in question_lower:
            return self._format_actions_answer(context)
        elif "meeting" in question_lower or "discussed" in question_lower:
            return self._format_meeting_answer(context)
        else:
            # General answer
            return self._format_general_answer(context)

    def _format_context_answer(self, context: Dict) -> str:
        """Format context/background answer"""
        return f"""
📄 **Source Context for Action**

**Meeting**: {context['meeting_name']}
**Source File**: `{context['source_file']}`

**Your Action**: {context['card_action']['action']}
**Owner**: {context['card_action']['owner']}
**Deadline**: {context['card_action']['deadline']}

**Related Decisions** ({len(context['related_decisions'])}):
{self._format_decisions_list(context['related_decisions'])}

**Other Action Items** ({len(context['related_actions'])}):
{self._format_actions_list(context['related_actions'])}

💡 **Full meeting summary available at**: {context['source_file']}
"""

    def _format_decisions_answer(self, context: Dict) -> str:
        """Format decisions answer"""
        decisions = context['related_decisions']
        if not decisions:
            return f"No decisions recorded in meeting {context['meeting_name']}"

        output = f"**Decisions from {context['meeting_name']}**:\n\n"
        output += self._format_decisions_list(decisions)
        return output

    def _format_actions_answer(self, context: Dict) -> str:
        """Format actions answer"""
        actions = context['related_actions']
        output = f"**All actions from {context['meeting_name']}**:\n\n"
        output += f"**Your action**:\n• {context['card_action']['action']} (Due: {context['card_action']['deadline']})\n\n"

        if actions:
            output += f"**Other team actions** ({len(actions)}):\n"
            output += self._format_actions_list(actions)

        return output

    def _format_meeting_answer(self, context: Dict) -> str:
        """Format meeting discussion answer"""
        summary = context['full_summary']

        # Extract executive summary
        import re
        exec_match = re.search(r'## 8\. Executive Summary\s+(.*?)(?=\n##|$)', summary, re.DOTALL)
        exec_summary = exec_match.group(1).strip() if exec_match else "No executive summary found"

        return f"""
**Meeting**: {context['meeting_name']}

**Executive Summary**:
{exec_summary}

**Key Outcomes**:
• {len(context['related_actions'])} action items assigned
• {len(context['related_decisions'])} decisions made

📄 **Full transcript summary**: {context['source_file']}
"""

    def _format_general_answer(self, context: Dict) -> str:
        """Format general answer"""
        return self._format_context_answer(context)

    def _format_decisions_list(self, decisions: List[Dict]) -> str:
        """Format decisions as list"""
        if not decisions:
            return "• None"
        return "\n".join([f"• {d['decision']}" for d in decisions])

    def _format_actions_list(self, actions: List[Dict]) -> str:
        """Format actions as list"""
        if not actions:
            return "• None"
        return "\n".join([f"• {a['action']} ({a['owner']}, Due: {a['deadline']})" for a in actions])


def main():
    """CLI interface"""
    import argparse

    parser = argparse.ArgumentParser(description="Trello Card Q&A System")
    parser.add_argument("card", help="Card name (or partial match)")
    parser.add_argument("--question", "-q", default="context",
                       help="Question type: context, decisions, actions, meeting")
    args = parser.parse_args()

    qa = TrelloCardQA()
    answer = qa.answer_question(args.card, args.question)
    print(answer)


if __name__ == "__main__":
    main()
