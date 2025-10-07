#!/usr/bin/env python3
"""
VTT Intelligence Processor - Personal Assistant Integration
Transforms meeting summaries into actionable intelligence across productivity systems

Integrations:
- Trello: Action item extraction and card creation
- Email RAG: Meeting summary indexing for semantic search
- Calendar: Meeting detection and prep note creation
- Daily Briefing: Proactive action item reminders

Author: Maia Personal Assistant Agent
Phase: 86.2 - VTT Intelligence Pipeline
Date: 2025-10-03
"""

import os
import sys
import json
import re
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import logging

# Setup path
MAIA_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(MAIA_ROOT))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class VTTIntelligenceProcessor:
    """Process VTT summaries into actionable intelligence"""

    def __init__(self):
        """Initialize intelligence processor"""
        self.data_dir = MAIA_ROOT / "claude" / "data"
        self.intelligence_db = self.data_dir / "vtt_intelligence.json"

        # Load existing intelligence
        self.intelligence = self._load_intelligence()

    def _load_intelligence(self) -> Dict:
        """Load intelligence database"""
        if self.intelligence_db.exists():
            with open(self.intelligence_db, 'r') as f:
                return json.load(f)
        return {
            "meetings": {},
            "action_items": [],
            "decisions": [],
            "contacts": {},
            "last_processed": None
        }

    def _save_intelligence(self):
        """Save intelligence database"""
        self.intelligence_db.parent.mkdir(parents=True, exist_ok=True)
        with open(self.intelligence_db, 'w') as f:
            json.dump(self.intelligence, f, indent=2)

    def process_summary(self, summary_file: Path) -> Dict[str, Any]:
        """
        Process a VTT summary file and extract intelligence

        Args:
            summary_file: Path to markdown summary file

        Returns:
            Intelligence extraction results
        """
        logger.info(f"Processing summary: {summary_file.name}")

        # Read summary
        with open(summary_file, 'r') as f:
            content = f.read()

        # Extract intelligence
        results = {
            "action_items": self._extract_action_items(content),
            "decisions": self._extract_decisions(content),
            "contacts": self._extract_contacts(content),
            "meetings_mentioned": self._extract_meeting_references(content),
            "summary_text": self._extract_executive_summary(content)
        }

        # Store in database
        meeting_id = summary_file.stem
        self.intelligence["meetings"][meeting_id] = {
            "file": str(summary_file),
            "processed_at": datetime.now().isoformat(),
            "results": results
        }

        # Update global lists with source file metadata
        for action in results["action_items"]:
            action["source_file"] = str(summary_file)
        for decision in results["decisions"]:
            decision["source_file"] = str(summary_file)

        self.intelligence["action_items"].extend(results["action_items"])
        self.intelligence["decisions"].extend(results["decisions"])

        # Update contacts
        for contact in results["contacts"]:
            if contact not in self.intelligence["contacts"]:
                self.intelligence["contacts"][contact] = {
                    "first_seen": datetime.now().isoformat(),
                    "meetings": []
                }
            self.intelligence["contacts"][contact]["meetings"].append(meeting_id)

        self.intelligence["last_processed"] = datetime.now().isoformat()
        self._save_intelligence()

        logger.info(f"✅ Extracted: {len(results['action_items'])} actions, {len(results['decisions'])} decisions")

        return results

    def _extract_action_items(self, content: str) -> List[Dict]:
        """Extract action items from summary"""
        action_items = []

        # Find action items table
        table_match = re.search(r'\| Owner \| Action \| Deadline \|.*?\n\|[-\|]+\|(.*?)(?=\n\n|\n##|$)',
                               content, re.DOTALL)

        if table_match:
            table_content = table_match.group(1)
            # Parse table rows
            rows = [r.strip() for r in table_content.split('\n') if r.strip()]

            for row in rows:
                parts = [p.strip() for p in row.split('|') if p.strip()]
                if len(parts) >= 3:
                    action_items.append({
                        "owner": parts[0],
                        "action": parts[1],
                        "deadline": parts[2],
                        "status": "pending",
                        "created_at": datetime.now().isoformat(),
                        "source": "vtt_summary"
                    })

        return action_items

    def _extract_decisions(self, content: str) -> List[Dict]:
        """Extract key decisions from summary"""
        decisions = []

        # Find architecture decisions section
        arch_match = re.search(r'## 4\. Architecture Decisions(.*?)(?=\n##|$)', content, re.DOTALL)
        if arch_match:
            arch_content = arch_match.group(1)
            # Extract bullet points starting with **
            decision_items = re.findall(r'\*\*([^*]+)\*\*:\s*([^\n]+)', arch_content)

            for title, description in decision_items:
                decisions.append({
                    "title": title.strip(),
                    "description": description.strip(),
                    "decided_at": datetime.now().isoformat(),
                    "source": "vtt_summary"
                })

        # Also check proposed solutions
        solutions_match = re.search(r'## 3\. Proposed Solutions(.*?)(?=\n##|$)', content, re.DOTALL)
        if solutions_match:
            solutions_content = solutions_match.group(1)
            # Extract ### headings as decisions
            solution_items = re.findall(r'### ([^\n]+)', solutions_content)

            for solution in solution_items:
                decisions.append({
                    "title": solution.strip(),
                    "description": f"Solution agreed: {solution.strip()}",
                    "decided_at": datetime.now().isoformat(),
                    "source": "vtt_summary"
                })

        return decisions

    def _extract_contacts(self, content: str) -> List[str]:
        """Extract mentioned contacts/people"""
        contacts = set()

        # Common name patterns in meetings (capitalized words)
        # Look in action items table first
        table_match = re.search(r'\| Owner \| Action \| Deadline \|.*?\n\|[-\|]+\|(.*?)(?=\n\n|\n##|$)',
                               content, re.DOTALL)

        if table_match:
            table_content = table_match.group(1)
            names = re.findall(r'\|\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\s*\|', table_content)
            contacts.update(names)

        # Also extract from participants section
        participants_match = re.search(r'\*\*Participants\*\*:\s*([^\n]+)', content)
        if participants_match:
            participants_text = participants_match.group(1)
            # Split by comma and extract names
            participant_names = re.findall(r'([A-Z][a-z]+\s+[A-Z][a-z]+)', participants_text)
            contacts.update(participant_names)

        return list(contacts)

    def _extract_meeting_references(self, content: str) -> List[Dict]:
        """Extract references to upcoming meetings"""
        meetings = []

        # Common meeting patterns
        patterns = [
            r'(Monday|Tuesday|Wednesday|Thursday|Friday)\s+(?:meeting|with)\s+([A-Z][a-z]+)',
            r'(fortnightly|weekly|monthly)\s+(?:meeting|catch-up|sync)',
            r'meeting\s+with\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)'
        ]

        for pattern in patterns:
            matches = re.finditer(pattern, content, re.IGNORECASE)
            for match in matches:
                meetings.append({
                    "reference": match.group(0),
                    "extracted_at": datetime.now().isoformat()
                })

        return meetings

    def _extract_executive_summary(self, content: str) -> str:
        """Extract executive summary section"""
        summary_match = re.search(r'## 8\. Executive Summary\s+(.*?)(?=\n##|$)', content, re.DOTALL)
        if summary_match:
            return summary_match.group(1).strip()
        return ""

    def get_pending_actions_for_owner(self, owner: str) -> List[Dict]:
        """Get pending action items for specific owner"""
        return [
            item for item in self.intelligence["action_items"]
            if item["owner"].lower() == owner.lower() and item["status"] == "pending"
        ]

    def get_recent_decisions(self, days: int = 7) -> List[Dict]:
        """Get decisions made in last N days"""
        cutoff = datetime.now() - timedelta(days=days)

        recent = []
        for decision in self.intelligence["decisions"]:
            decided_at = datetime.fromisoformat(decision["decided_at"])
            if decided_at >= cutoff:
                recent.append(decision)

        return recent

    def export_for_trello(self, owner: str) -> List[Dict]:
        """
        Export action items formatted for Trello card creation

        Args:
            owner: Filter by owner name

        Returns:
            List of Trello card specs
        """
        actions = self.get_pending_actions_for_owner(owner)

        trello_cards = []
        for action in actions:
            # Get source meeting name from action
            meeting_name = action.get('source', 'Unknown')

            # Look up source file from meetings dict
            source_file = 'Unknown'
            if meeting_name in self.intelligence['meetings']:
                source_file = self.intelligence['meetings'][meeting_name]['file']

            # Format meeting name for display
            display_name = meeting_name.replace('_', ' ')

            # Create enhanced description with source link
            desc = f"""**Owner**: {action['owner']}
**Deadline**: {action['deadline']}
**Source Meeting**: {display_name}
**Source File**: `{source_file}`
**Created**: {action['created_at']}

---
📄 **Source Context**: Check the source file above for full meeting context, decisions, and related action items.

🔍 **Ask Maia**: "What was discussed in {display_name}?" or "Show me context for this action"
"""

            trello_cards.append({
                "name": action["action"][:255],  # Trello name limit
                "desc": desc,
                "due": self._parse_deadline_to_iso(action["deadline"]),
                "labels": ["meeting-action"]
            })

        return trello_cards

    def _parse_deadline_to_iso(self, deadline_str: str) -> Optional[str]:
        """Parse deadline string to ISO format"""
        # Simple parsing for common patterns
        deadline_lower = deadline_str.lower()

        if "next week" in deadline_lower:
            target = datetime.now() + timedelta(days=7)
            return target.isoformat()
        elif "monday" in deadline_lower:
            # Find next Monday
            days_ahead = (0 - datetime.now().weekday()) % 7
            if days_ahead == 0:
                days_ahead = 7
            target = datetime.now() + timedelta(days=days_ahead)
            return target.isoformat()
        elif "immediate" in deadline_lower or "asap" in deadline_lower:
            return datetime.now().isoformat()

        return None

    def export_for_daily_briefing(self) -> Dict[str, Any]:
        """Export intelligence for daily briefing integration"""
        return {
            "pending_actions": len([a for a in self.intelligence["action_items"] if a["status"] == "pending"]),
            "recent_decisions": self.get_recent_decisions(days=3),
            "active_contacts": list(self.intelligence["contacts"].keys())[-10:],
            "last_meeting": max(self.intelligence["meetings"].values(),
                               key=lambda x: x["processed_at"]) if self.intelligence["meetings"] else None
        }


def main():
    """CLI interface"""
    import argparse

    parser = argparse.ArgumentParser(description="VTT Intelligence Processor")
    parser.add_argument("command", choices=["process", "actions", "decisions", "export-trello", "briefing"],
                       help="Command to execute")
    parser.add_argument("--file", help="VTT summary file to process")
    parser.add_argument("--owner", default="Naythan", help="Filter by owner name")
    parser.add_argument("--days", type=int, default=7, help="Days to look back")

    args = parser.parse_args()

    processor = VTTIntelligenceProcessor()

    if args.command == "process":
        if not args.file:
            print("❌ Error: --file required for process command")
            sys.exit(1)

        summary_file = Path(args.file)
        if not summary_file.exists():
            print(f"❌ Error: File not found: {summary_file}")
            sys.exit(1)

        results = processor.process_summary(summary_file)
        print(f"\n✅ Processing Complete:")
        print(f"   • Action Items: {len(results['action_items'])}")
        print(f"   • Decisions: {len(results['decisions'])}")
        print(f"   • Contacts: {len(results['contacts'])}")
        print(f"   • Meeting References: {len(results['meetings_mentioned'])}")

    elif args.command == "actions":
        actions = processor.get_pending_actions_for_owner(args.owner)
        print(f"\n📋 Pending Actions for {args.owner}: {len(actions)}")
        for i, action in enumerate(actions, 1):
            print(f"\n{i}. {action['action']}")
            print(f"   Deadline: {action['deadline']}")
            print(f"   Created: {action['created_at']}")

    elif args.command == "decisions":
        decisions = processor.get_recent_decisions(days=args.days)
        print(f"\n🎯 Decisions (Last {args.days} days): {len(decisions)}")
        for i, decision in enumerate(decisions, 1):
            print(f"\n{i}. {decision['title']}")
            print(f"   {decision['description']}")

    elif args.command == "export-trello":
        cards = processor.export_for_trello(args.owner)
        print(f"\n📌 Trello Cards for {args.owner}: {len(cards)}")
        print(json.dumps(cards, indent=2))

    elif args.command == "briefing":
        briefing = processor.export_for_daily_briefing()
        print("\n📊 Daily Briefing Intelligence:")
        print(json.dumps(briefing, indent=2))


if __name__ == "__main__":
    main()
