#!/usr/bin/env python3
"""
Confluence Intelligence Processor - Executive Command Center
Extracts actionable intelligence from Confluence pages for executive decision-making

Author: Maia Personal Assistant Agent
Phase: 86.4 - Executive Command Center
Date: 2025-10-03
"""

import os
import sys
import json
import re
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
import logging

MAIA_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(MAIA_ROOT))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ConfluenceIntelligenceProcessor:
    """Extract executive intelligence from Confluence pages"""

    def __init__(self):
        """Initialize processor"""
        self.data_dir = MAIA_ROOT / "claude" / "data"
        self.intelligence_db = self.data_dir / "confluence_intelligence.json"
        self.intelligence = self._load_intelligence()

    def _load_intelligence(self) -> Dict:
        """Load intelligence database"""
        if self.intelligence_db.exists():
            with open(self.intelligence_db, 'r') as f:
                return json.load(f)
        return {
            "pages": {},
            "action_items": [],
            "questions": [],
            "strategic_initiatives": [],
            "decisions_needed": [],
            "team_members": [],
            "tools_systems": [],
            "last_processed": None
        }

    def _save_intelligence(self):
        """Save intelligence database"""
        self.intelligence_db.parent.mkdir(parents=True, exist_ok=True)
        with open(self.intelligence_db, 'w') as f:
            json.dump(self.intelligence, f, indent=2)

    def process_page(self, page_file: Path, page_url: str = None) -> Dict[str, Any]:
        """
        Process Confluence page and extract intelligence

        Args:
            page_file: Path to markdown summary of page
            page_url: Optional URL to Confluence page

        Returns:
            Extracted intelligence
        """
        logger.info(f"Processing Confluence page: {page_file.name}")

        with open(page_file, 'r') as f:
            content = f.read()

        results = {
            "action_items": self._extract_action_items(content),
            "questions": self._extract_questions(content),
            "strategic_initiatives": self._extract_strategic_items(content),
            "decisions_needed": self._extract_decisions_needed(content),
            "team_members": self._extract_team_members(content),
            "tools_systems": self._extract_tools_systems(content),
            "key_themes": self._extract_key_themes(content)
        }

        # Store in database
        page_id = page_file.stem
        self.intelligence["pages"][page_id] = {
            "file": str(page_file),
            "url": page_url,
            "processed_at": datetime.now().isoformat(),
            "results": results
        }

        # Update global lists
        self.intelligence["action_items"].extend(results["action_items"])
        self.intelligence["questions"].extend(results["questions"])
        self.intelligence["strategic_initiatives"].extend(results["strategic_initiatives"])
        self.intelligence["decisions_needed"].extend(results["decisions_needed"])

        self.intelligence["last_processed"] = datetime.now().isoformat()
        self._save_intelligence()

        logger.info(f"✅ Extracted: {len(results['action_items'])} actions, "
                   f"{len(results['questions'])} questions, "
                   f"{len(results['strategic_initiatives'])} strategic items")

        return results

    def _extract_action_items(self, content: str) -> List[Dict]:
        """Extract action items"""
        actions = []

        # Pattern 1: Numbered items followed by action verbs
        action_patterns = [
            r'^\d+\.\s+(.*?(?:review|follow up|check|setup|confirm|order).*?)$',
            r'^-\s+(.*?(?:review|follow up|check|setup|confirm|order).*?)$',
            r'^\*\s+(.*?(?:review|follow up|check|setup|confirm|order).*?)$'
        ]

        lines = content.split('\n')
        for line in lines:
            line = line.strip()
            for pattern in action_patterns:
                match = re.search(pattern, line, re.IGNORECASE)
                if match:
                    action_text = match.group(1).strip()
                    if len(action_text) > 10:  # Filter noise
                        actions.append({
                            "action": action_text,
                            "category": self._categorize_action(action_text),
                            "priority": self._estimate_priority(action_text),
                            "created_at": datetime.now().isoformat(),
                            "status": "pending"
                        })
                    break

        return actions

    def _extract_questions(self, content: str) -> List[Dict]:
        """Extract open questions"""
        questions = []

        # Pattern: Lines ending with '?'
        lines = content.split('\n')
        for line in lines:
            line = line.strip()
            if '?' in line and len(line) > 10:
                questions.append({
                    "question": line,
                    "category": self._categorize_question(line),
                    "priority": self._estimate_priority(line),
                    "created_at": datetime.now().isoformat(),
                    "status": "unanswered"
                })

        return questions

    def _extract_strategic_items(self, content: str) -> List[Dict]:
        """Extract strategic initiatives"""
        strategic = []

        strategic_keywords = [
            'pod', 'okr', 'kpi', 'engagement', 'culture', 'retro',
            'hiring', 'sponsorship', 'training', 'balanced score card',
            'service catalogue', 'change control', 'cab'
        ]

        lines = content.split('\n')
        for line in lines:
            line_lower = line.lower().strip()
            if any(keyword in line_lower for keyword in strategic_keywords):
                if len(line.strip()) > 15:
                    strategic.append({
                        "initiative": line.strip(),
                        "category": "strategic",
                        "created_at": datetime.now().isoformat(),
                        "status": "identified"
                    })

        return strategic

    def _extract_decisions_needed(self, content: str) -> List[Dict]:
        """Extract items requiring decisions"""
        decisions = []

        decision_keywords = [
            'budget', 'approval', 'confirm', 'decide', 'choose',
            'converting to', 'plan for', 'what do we'
        ]

        lines = content.split('\n')
        for line in lines:
            line_lower = line.lower().strip()
            if any(keyword in line_lower for keyword in decision_keywords):
                if len(line.strip()) > 15:
                    decisions.append({
                        "decision": line.strip(),
                        "urgency": self._estimate_urgency(line),
                        "created_at": datetime.now().isoformat(),
                        "status": "pending"
                    })

        return decisions

    def _extract_team_members(self, content: str) -> List[str]:
        """Extract team member names"""
        members = set()

        # Pattern: "Name | Orro" or "Name:" or capitalized names
        name_patterns = [
            r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\s*\|\s*Orro',
            r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?):'
        ]

        for pattern in name_patterns:
            matches = re.finditer(pattern, content)
            for match in matches:
                name = match.group(1).strip()
                if len(name.split()) <= 3:  # Reasonable name length
                    members.add(name)

        return list(members)

    def _extract_tools_systems(self, content: str) -> List[str]:
        """Extract tools and systems mentioned"""
        tools = set()

        tool_patterns = [
            r'\b([A-Z][a-z]+(?:[A-Z][a-z]+)*)\b(?:\s*[-:]|\s+(?:suite|platform|system|tool|software))',
            r'\b(IT\s*Glue|One\s*Note|OTC|Jira|Confluence|Trello)\b'
        ]

        for pattern in tool_patterns:
            matches = re.finditer(pattern, content, re.IGNORECASE)
            for match in matches:
                tool = match.group(1).strip()
                if len(tool) > 2:
                    tools.add(tool)

        return list(tools)

    def _extract_key_themes(self, content: str) -> List[str]:
        """Extract key themes from headers"""
        themes = []

        # Extract markdown headers
        header_matches = re.finditer(r'^#+\s+(.+)$', content, re.MULTILINE)
        for match in header_matches:
            theme = match.group(1).strip()
            if 'theme' in theme.lower() or 'key' in theme.lower():
                continue  # Skip meta headers
            themes.append(theme)

        return themes[:10]  # Top 10

    def _categorize_action(self, text: str) -> str:
        """Categorize action item"""
        text_lower = text.lower()

        if any(word in text_lower for word in ['review', 'check', 'confirm']):
            return "review"
        elif any(word in text_lower for word in ['follow up', 'follow-up', 'followup']):
            return "follow-up"
        elif any(word in text_lower for word in ['setup', 'set up', 'configure']):
            return "setup"
        elif any(word in text_lower for word in ['order', 'purchase', 'buy']):
            return "procurement"
        else:
            return "general"

    def _categorize_question(self, text: str) -> str:
        """Categorize question"""
        text_lower = text.lower()

        if any(word in text_lower for word in ['system', 'tool', 'software', 'platform']):
            return "systems"
        elif any(word in text_lower for word in ['team', 'people', 'who', 'hiring']):
            return "team"
        elif any(word in text_lower for word in ['process', 'how', 'workflow']):
            return "process"
        elif any(word in text_lower for word in ['budget', 'cost', 'expense', 'allowance']):
            return "financial"
        else:
            return "general"

    def _estimate_priority(self, text: str) -> str:
        """Estimate priority from text"""
        text_lower = text.lower()

        if any(word in text_lower for word in ['urgent', 'asap', 'immediate', 'critical']):
            return "high"
        elif any(word in text_lower for word in ['soon', 'next week', 'follow up']):
            return "medium"
        else:
            return "low"

    def _estimate_urgency(self, text: str) -> str:
        """Estimate urgency of decision"""
        text_lower = text.lower()

        if any(word in text_lower for word in ['budget', 'approval', 'confirm']):
            return "high"
        elif any(word in text_lower for word in ['plan', 'converting', 'what do we']):
            return "medium"
        else:
            return "low"

    def export_for_trello(self, owner: str = "Naythan") -> Dict[str, List[Dict]]:
        """Export intelligence for Trello card creation"""

        trello_export = {
            "strategic": [],
            "operational": [],
            "questions": [],
            "decisions": []
        }

        # Strategic initiatives
        for item in self.intelligence["strategic_initiatives"]:
            trello_export["strategic"].append({
                "name": item["initiative"][:255],
                "desc": f"**Type**: Strategic Initiative\n**Status**: {item['status']}\n**Identified**: {item['created_at']}",
                "labels": ["strategic"]
            })

        # Action items
        for item in self.intelligence["action_items"]:
            trello_export["operational"].append({
                "name": item["action"][:255],
                "desc": f"**Category**: {item['category']}\n**Priority**: {item['priority']}\n**Created**: {item['created_at']}",
                "labels": ["action", item["priority"]]
            })

        # Questions
        for item in self.intelligence["questions"]:
            trello_export["questions"].append({
                "name": item["question"][:255],
                "desc": f"**Category**: {item['category']}\n**Priority**: {item['priority']}\n**Created**: {item['created_at']}",
                "labels": ["question", item["category"]]
            })

        # Decisions
        for item in self.intelligence["decisions_needed"]:
            trello_export["decisions"].append({
                "name": item["decision"][:255],
                "desc": f"**Urgency**: {item['urgency']}\n**Created**: {item['created_at']}",
                "labels": ["decision", item["urgency"]]
            })

        return trello_export

    def get_executive_summary(self) -> Dict:
        """Get executive summary for dashboard"""
        return {
            "total_action_items": len(self.intelligence["action_items"]),
            "pending_questions": len([q for q in self.intelligence["questions"] if q["status"] == "unanswered"]),
            "strategic_initiatives": len(self.intelligence["strategic_initiatives"]),
            "decisions_needed": len(self.intelligence["decisions_needed"]),
            "team_members_identified": len(set(self.intelligence.get("team_members", []))),
            "last_updated": self.intelligence.get("last_processed")
        }


def main():
    """CLI interface"""
    import argparse

    parser = argparse.ArgumentParser(description="Confluence Intelligence Processor")
    parser.add_argument("command", choices=["process", "summary", "export-trello"],
                       help="Command to execute")
    parser.add_argument("--file", help="Confluence page file")
    parser.add_argument("--url", help="Confluence page URL")

    args = parser.parse_args()

    processor = ConfluenceIntelligenceProcessor()

    if args.command == "process":
        if not args.file:
            print("❌ Error: --file required")
            sys.exit(1)

        results = processor.process_page(Path(args.file), args.url)
        print(f"\n✅ Processing Complete:")
        print(f"   • Action Items: {len(results['action_items'])}")
        print(f"   • Questions: {len(results['questions'])}")
        print(f"   • Strategic Items: {len(results['strategic_initiatives'])}")
        print(f"   • Decisions Needed: {len(results['decisions_needed'])}")

    elif args.command == "summary":
        summary = processor.get_executive_summary()
        print("\n📊 Executive Summary:")
        print(json.dumps(summary, indent=2))

    elif args.command == "export-trello":
        export = processor.export_for_trello()
        print("\n📌 Trello Export:")
        print(f"   • Strategic: {len(export['strategic'])} cards")
        print(f"   • Operational: {len(export['operational'])} cards")
        print(f"   • Questions: {len(export['questions'])} cards")
        print(f"   • Decisions: {len(export['decisions'])} cards")


if __name__ == "__main__":
    main()
