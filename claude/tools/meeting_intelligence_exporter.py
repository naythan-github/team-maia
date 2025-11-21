#!/usr/bin/env python3
"""
Meeting Intelligence Exporter - Export to Confluence and Trello

Automatically exports meeting intelligence to:
- Confluence: Meeting summaries as pages
- Trello: Action items as cards

Usage:
    # Export to Confluence only
    python3 meeting_intelligence_exporter.py transcript.md --confluence-space "TEAM"

    # Export to Trello only
    python3 meeting_intelligence_exporter.py transcript.md --trello-board "board_id"

    # Export to both
    python3 meeting_intelligence_exporter.py transcript.md \
        --confluence-space "TEAM" \
        --trello-board "board_id"

Author: Maia System
Created: 2025-11-21
Phase: 164 - Meeting Intelligence Integration
"""

import os
import sys
import json
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional

# Add Maia root to path
MAIA_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(MAIA_ROOT))

from claude.tools.meeting_intelligence_processor import MeetingIntelligenceProcessor
from claude.tools.confluence_client import ConfluenceClient
# Trello integration would go here when available


class MeetingIntelligenceExporter:
    """Export meeting intelligence to Confluence and Trello"""

    def __init__(self):
        """Initialize exporters"""
        self.processor = MeetingIntelligenceProcessor()
        self.confluence = None
        self.trello = None

    def _init_confluence(self):
        """Lazy init Confluence client"""
        if self.confluence is None:
            self.confluence = ConfluenceClient()
        return self.confluence

    def export_to_confluence(
        self,
        intelligence_results: Dict,
        space_key: str,
        parent_page_title: Optional[str] = None
    ) -> str:
        """
        Export meeting intelligence to Confluence page

        Args:
            intelligence_results: Output from MeetingIntelligenceProcessor
            space_key: Confluence space key (e.g., "TEAM", "Orro")
            parent_page_title: Optional parent page for organization

        Returns:
            URL of created page
        """
        client = self._init_confluence()

        # Extract metadata
        metadata = intelligence_results.get("metadata", {})
        title = metadata.get("title", "Meeting")
        date = metadata.get("date", datetime.now().strftime("%Y-%m-%d"))

        # Build page title
        page_title = f"Meeting: {title} ({date})"

        # Build markdown content
        markdown = self._build_confluence_markdown(intelligence_results)

        # Create page
        try:
            url = client.create_page_from_markdown(
                space_key=space_key,
                title=page_title,
                markdown_content=markdown
            )
            print(f"✅ Confluence page created: {url}")
            return url
        except Exception as e:
            print(f"❌ Confluence export failed: {e}")
            raise

    def _build_confluence_markdown(self, results: Dict) -> str:
        """Build formatted markdown for Confluence"""
        metadata = results.get("metadata", {})
        title = metadata.get("title", "Meeting")
        date = metadata.get("date", "Unknown")
        session_id = metadata.get("session_id", "")

        lines = []

        # Header with metadata
        lines.append(f"# Meeting: {title}")
        lines.append("")
        lines.append(f"**Date**: {date}")
        if session_id:
            lines.append(f"**Session ID**: {session_id}")
        lines.append(f"**Processed**: {results.get('timestamp', '')}")
        lines.append("")
        lines.append("---")
        lines.append("")

        # Executive Summary
        if "summary" in results and results["summary"].get("success"):
            lines.append("## Executive Summary")
            lines.append("")
            summary = results["summary"]
            for i, bullet in enumerate(summary.get("bullet_points", []), 1):
                lines.append(f"{i}. {bullet}")
            lines.append("")
            lines.append("---")
            lines.append("")

        # Action Items
        if "action_items" in results and results["action_items"].get("success"):
            lines.append("## Action Items")
            lines.append("")
            actions = results["action_items"]["action_items"]

            if actions:
                for i, item in enumerate(actions, 1):
                    lines.append(f"### {i}. {item['task']}")
                    if item.get('assignee'):
                        lines.append(f"- **Assignee**: {item['assignee']}")
                    if item.get('deadline'):
                        lines.append(f"- **Deadline**: {item['deadline']}")
                    if item.get('priority'):
                        lines.append(f"- **Priority**: {item['priority']}")
                    if item.get('context'):
                        lines.append(f"- **Context**: {item['context']}")
                    lines.append("")
            else:
                lines.append("No action items identified.")
                lines.append("")

            lines.append("---")
            lines.append("")

        # Key Topics
        if "keywords" in results and results["keywords"].get("success"):
            lines.append("## Key Topics Discussed")
            lines.append("")
            keywords = results["keywords"]["keywords"]
            for i, keyword in enumerate(keywords, 1):
                lines.append(f"{i}. {keyword}")
            lines.append("")
            lines.append("---")
            lines.append("")

        # Footer
        lines.append("## Processing Metadata")
        lines.append("")
        lines.append(f"- **Total Processing Time**: {results.get('total_latency_seconds', 0)}s")
        lines.append(f"- **Word Count**: {results.get('word_count', 0)}")
        lines.append("")
        lines.append("*Generated automatically by Maia Meeting Intelligence System*")

        return "\n".join(lines)

    def export_to_trello(
        self,
        intelligence_results: Dict,
        board_id: str,
        list_name: str = "Action Items"
    ) -> List[str]:
        """
        Export action items to Trello board

        Args:
            intelligence_results: Output from MeetingIntelligenceProcessor
            board_id: Trello board ID
            list_name: Name of list to add cards to

        Returns:
            List of created card URLs
        """
        # TODO: Implement when Trello integration is configured
        print("⚠️  Trello export not yet implemented")
        print("   Action items available in JSON for manual import")

        # Show what would be exported
        if "action_items" in intelligence_results:
            actions = intelligence_results["action_items"].get("action_items", [])
            print(f"\n📋 {len(actions)} action items ready for Trello:")
            for i, item in enumerate(actions, 1):
                print(f"   {i}. {item['task']}")
                if item.get('assignee'):
                    print(f"      → Assignee: {item['assignee']}")

        return []

    def export_intelligence_file(
        self,
        intelligence_json_path: str,
        confluence_space: Optional[str] = None,
        trello_board: Optional[str] = None,
        confluence_parent: Optional[str] = None
    ) -> Dict:
        """
        Export from existing intelligence JSON file

        Args:
            intelligence_json_path: Path to *_intelligence.json file
            confluence_space: Confluence space key (optional)
            trello_board: Trello board ID (optional)
            confluence_parent: Parent page title in Confluence (optional)

        Returns:
            Dict with export results
        """
        # Load intelligence file
        with open(intelligence_json_path, 'r') as f:
            intelligence = json.load(f)

        results = {
            "confluence_url": None,
            "trello_cards": []
        }

        # Export to Confluence
        if confluence_space:
            try:
                url = self.export_to_confluence(
                    intelligence,
                    confluence_space
                )
                results["confluence_url"] = url
            except Exception as e:
                print(f"❌ Confluence export failed: {e}")

        # Export to Trello
        if trello_board:
            try:
                cards = self.export_to_trello(
                    intelligence,
                    trello_board
                )
                results["trello_cards"] = cards
            except Exception as e:
                print(f"❌ Trello export failed: {e}")

        return results

    def process_and_export(
        self,
        transcript_path: str,
        confluence_space: Optional[str] = None,
        trello_board: Optional[str] = None,
        confluence_parent: Optional[str] = None
    ) -> Dict:
        """
        Process transcript and export in one step

        Args:
            transcript_path: Path to transcript Markdown file
            confluence_space: Confluence space key (optional)
            trello_board: Trello board ID (optional)
            confluence_parent: Parent page in Confluence (optional)

        Returns:
            Dict with processing + export results
        """
        print(f"\n{'='*80}")
        print("📋 MEETING INTELLIGENCE EXPORT")
        print(f"{'='*80}\n")

        # Process transcript
        print("🔄 Processing transcript...")
        intelligence = self.processor.process_transcript(transcript_path)

        # Save intelligence JSON
        json_path = self.processor.save_intelligence(intelligence)

        # Export
        results = {
            "intelligence_json": str(json_path),
            "confluence_url": None,
            "trello_cards": []
        }

        # Export to Confluence
        if confluence_space:
            print(f"\n🔄 Exporting to Confluence space: {confluence_space}")
            try:
                url = self.export_to_confluence(
                    intelligence,
                    confluence_space
                )
                results["confluence_url"] = url
            except Exception as e:
                print(f"❌ Confluence export failed: {e}")

        # Export to Trello
        if trello_board:
            print(f"\n🔄 Exporting to Trello board: {trello_board}")
            try:
                cards = self.export_to_trello(
                    intelligence,
                    trello_board
                )
                results["trello_cards"] = cards
            except Exception as e:
                print(f"❌ Trello export failed: {e}")

        print(f"\n{'='*80}")
        print("✅ EXPORT COMPLETE")
        print(f"{'='*80}\n")

        # Summary
        print("📊 Export Summary:")
        print(f"   Intelligence JSON: {results['intelligence_json']}")
        if results['confluence_url']:
            print(f"   Confluence: {results['confluence_url']}")
        if results['trello_cards']:
            print(f"   Trello: {len(results['trello_cards'])} cards created")

        return results


def main():
    """CLI entry point"""
    parser = argparse.ArgumentParser(
        description="Export meeting intelligence to Confluence and/or Trello"
    )
    parser.add_argument(
        'transcript',
        help='Path to transcript Markdown file or intelligence JSON'
    )
    parser.add_argument(
        '--confluence-space',
        help='Confluence space key (e.g., "TEAM", "Orro")'
    )
    parser.add_argument(
        '--confluence-parent',
        help='Parent page title in Confluence (for organization)'
    )
    parser.add_argument(
        '--trello-board',
        help='Trello board ID'
    )
    parser.add_argument(
        '--from-json',
        action='store_true',
        help='Input is intelligence JSON (not transcript)'
    )

    args = parser.parse_args()

    # Validate at least one export target
    if not args.confluence_space and not args.trello_board:
        print("❌ Error: Must specify at least one export target")
        print("   Use --confluence-space or --trello-board")
        sys.exit(1)

    exporter = MeetingIntelligenceExporter()

    try:
        if args.from_json:
            # Export from existing intelligence file
            results = exporter.export_intelligence_file(
                args.transcript,
                confluence_space=args.confluence_space,
                trello_board=args.trello_board,
                confluence_parent=args.confluence_parent
            )
        else:
            # Process transcript and export
            results = exporter.process_and_export(
                args.transcript,
                confluence_space=args.confluence_space,
                trello_board=args.trello_board,
                confluence_parent=args.confluence_parent
            )

        print("\n✅ Success!")
        sys.exit(0)

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
