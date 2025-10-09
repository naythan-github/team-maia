#!/usr/bin/env python3
"""
Conversation Save Helper - Automated Conversation Persistence

Helper script for automated conversation saving with minimal user friction.
Integrates conversation_detector.py with conversation_rag_ollama.py.

Author: Maia System
Created: 2025-10-09 (Phase 102)
"""

import sys
import json
import re
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime

# Add Maia root to path
MAIA_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(MAIA_ROOT))

try:
    from claude.hooks.conversation_detector import ConversationDetector
    from claude.tools.conversation_rag_ollama import ConversationRAG
except ImportError as e:
    print(f"❌ Import error: {e}")
    print(f"   Make sure conversation_detector.py and conversation_rag_ollama.py exist")
    sys.exit(1)


class ConversationSaveHelper:
    """Helper for automated conversation saving"""

    def __init__(self):
        self.detector = ConversationDetector()
        self.rag = ConversationRAG()
        self.state_file = Path.home() / ".maia" / "conversation_save_state.json"
        self.state_file.parent.mkdir(parents=True, exist_ok=True)

    def load_state(self) -> Dict:
        """Load conversation save state"""
        if self.state_file.exists():
            with open(self.state_file, 'r') as f:
                return json.load(f)
        return {
            "last_prompt_time": None,
            "conversation_buffer": [],
            "dismissed_count": 0,
            "saved_count": 0
        }

    def save_state(self, state: Dict):
        """Save conversation save state"""
        with open(self.state_file, 'w') as f:
            json.dump(state, f, indent=2)

    def analyze_for_saving(self, conversation_text: str, turn_count: int = 1) -> Dict:
        """Analyze if conversation should trigger save prompt"""
        return self.detector.analyze_conversation(conversation_text, turn_count=turn_count)

    def auto_extract_summary(self, conversation_text: str, analysis: Dict) -> Dict:
        """
        Automatically extract topic, decisions, and tags from conversation

        Returns dict with: topic, summary, key_decisions, tags
        """

        # Extract topic (first substantial sentence or detected topics)
        lines = [l.strip() for l in conversation_text.split('\n') if l.strip()]
        topic_line = lines[0] if lines else "Conversation Summary"

        # Limit topic length
        if len(topic_line) > 100:
            topic_line = topic_line[:97] + "..."

        # Extract key sentences as decisions/recommendations
        decision_patterns = [
            r"(?:Recommendation|Decision|Approach|Strategy|Plan):\s*(.+?)(?:\n|$)",
            r"[-•]\s*(.+?)(?:\n|$)",  # Bullet points
            r"(?:should|will|recommend|propose|suggest)\s+(.+?)(?:\.|;|\n|$)"
        ]

        key_decisions = []
        for pattern in decision_patterns:
            matches = re.findall(pattern, conversation_text, re.IGNORECASE | re.MULTILINE)
            key_decisions.extend([m.strip() for m in matches if len(m.strip()) > 10])

        # Deduplicate and limit
        key_decisions = list(dict.fromkeys(key_decisions))[:7]  # Max 7 key points

        if not key_decisions:
            key_decisions = ["See conversation summary for details"]

        # Extract tags from detector
        _, tags = self.detector.extract_topics_and_tags(conversation_text)

        # Add timestamp to topic if not already there
        if not re.search(r'\d{4}-\d{2}-\d{2}', topic_line):
            date_str = datetime.now().strftime('%Y-%m-%d')
            topic_line = f"{topic_line} ({date_str})"

        return {
            "topic": topic_line,
            "summary": conversation_text[:1000],  # First 1000 chars as summary
            "key_decisions": key_decisions,
            "tags": tags
        }

    def quick_save(self, conversation_text: str, analysis: Optional[Dict] = None) -> str:
        """
        Quick save with auto-extraction

        Returns conversation_id on success, None on failure
        """
        if analysis is None:
            analysis = self.analyze_for_saving(conversation_text)

        # Auto-extract conversation data
        extracted = self.auto_extract_summary(conversation_text, analysis)

        try:
            conv_id = self.rag.save_conversation(
                topic=extracted["topic"],
                summary=extracted["summary"],
                key_decisions=extracted["key_decisions"],
                tags=extracted["tags"]
            )

            # Update state
            state = self.load_state()
            state["saved_count"] = state.get("saved_count", 0) + 1
            state["last_save_time"] = datetime.now().isoformat()
            self.save_state(state)

            return conv_id

        except Exception as e:
            print(f"❌ Error saving conversation: {e}")
            return None

    def should_prompt(self, analysis: Dict) -> bool:
        """Determine if we should prompt user to save"""

        # Don't prompt for trivial conversations
        if not analysis['significant']:
            return False

        # Always prompt for "definitely_save" recommendations
        if analysis['recommendation'] == 'definitely_save':
            return True

        # For "recommend_save", prompt if score > 35
        if analysis['recommendation'] == 'recommend_save' and analysis['score'] > 35:
            return True

        return False

    def generate_prompt_message(self, analysis: Dict, conversation_preview: str) -> str:
        """Generate save prompt for user"""
        return self.detector.generate_save_prompt(analysis, conversation_preview)


def main():
    """CLI interface"""
    import argparse

    parser = argparse.ArgumentParser(description="Conversation Save Helper")
    parser.add_argument("--analyze", help="Analyze conversation text from file")
    parser.add_argument("--quick-save", help="Quick save conversation from file")
    parser.add_argument("--stats", action="store_true", help="Show save statistics")

    args = parser.parse_args()

    helper = ConversationSaveHelper()

    if args.stats:
        state = helper.load_state()
        rag_stats = helper.rag.get_stats()

        print("\n📊 Conversation Save Statistics\n")
        print(f"Total Saved: {rag_stats['total_conversations']}")
        print(f"Auto-saves: {state.get('saved_count', 0)}")
        print(f"Dismissed: {state.get('dismissed_count', 0)}")
        print(f"Last Save: {state.get('last_save_time', 'Never')}")
        print(f"Storage: {rag_stats['storage_path']}\n")

    elif args.analyze:
        file_path = Path(args.analyze)
        if not file_path.exists():
            print(f"❌ File not found: {file_path}")
            sys.exit(1)

        conversation_text = file_path.read_text()
        analysis = helper.analyze_for_saving(conversation_text)

        print(f"\n📊 Analysis Results\n")
        print(f"Significant: {'✅ Yes' if analysis['significant'] else '❌ No'}")
        print(f"Score: {analysis['score']}/100")
        print(f"Recommendation: {analysis['recommendation']}")

        if helper.should_prompt(analysis):
            print(f"\n{helper.generate_prompt_message(analysis, conversation_text)}")

    elif args.quick_save:
        file_path = Path(args.quick_save)
        if not file_path.exists():
            print(f"❌ File not found: {file_path}")
            sys.exit(1)

        conversation_text = file_path.read_text()
        analysis = helper.analyze_for_saving(conversation_text)

        print(f"\n💾 Quick Save\n")
        print(f"Significance Score: {analysis['score']}/100")

        extracted = helper.auto_extract_summary(conversation_text, analysis)
        print(f"\nExtracted Topic: {extracted['topic']}")
        print(f"Key Decisions: {len(extracted['key_decisions'])}")
        print(f"Tags: {', '.join(extracted['tags'])}")

        conv_id = helper.quick_save(conversation_text, analysis)

        if conv_id:
            print(f"\n✅ Saved! Conversation ID: {conv_id}")
        else:
            print(f"\n❌ Save failed")

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
