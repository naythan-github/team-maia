#!/usr/bin/env python3
"""
VTT Intelligence Pipeline - Master Orchestrator
Complete automation: VTT Summary → Intelligence Extraction → Trello + RAG + Briefing

Workflow:
1. Process VTT summary → Extract intelligence (actions, decisions, contacts)
2. Push action items → Trello cards
3. Index summary → Meeting RAG for semantic search
4. Update daily briefing → Proactive reminders

Author: Maia Personal Assistant Agent
Phase: 86.2 - VTT Intelligence Automation Complete
Date: 2025-10-03
"""

import os
import sys
from pathlib import Path
from typing import Dict, Optional
import logging
import json

MAIA_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(MAIA_ROOT))

from claude.tools.vtt_intelligence_processor import VTTIntelligenceProcessor
from claude.tools.vtt_to_trello import VTTTrelloIntegration
from claude.tools.vtt_to_email_rag import VTTEmailRAGIntegration

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class VTTIntelligencePipeline:
    """Master orchestrator for VTT intelligence automation"""

    def __init__(self, owner: str = "Naythan", trello_board: Optional[str] = None):
        """
        Initialize pipeline

        Args:
            owner: Owner name for action item filtering
            trello_board: Default Trello board ID
        """
        self.owner = owner
        self.trello_board = trello_board

        # Initialize components
        self.intelligence = VTTIntelligenceProcessor()
        self.trello_integration = VTTTrelloIntegration()
        self.rag_integration = VTTEmailRAGIntegration()

        # Pipeline state
        self.pipeline_db = MAIA_ROOT / "claude" / "data" / "vtt_pipeline_state.json"
        self.state = self._load_state()

    def _load_state(self) -> Dict:
        """Load pipeline state"""
        if self.pipeline_db.exists():
            with open(self.pipeline_db, 'r') as f:
                return json.load(f)
        return {"processed_summaries": {}}

    def _save_state(self):
        """Save pipeline state"""
        self.pipeline_db.parent.mkdir(parents=True, exist_ok=True)
        with open(self.pipeline_db, 'w') as f:
            json.dump(self.state, f, indent=2)

    def process_summary_complete(self, summary_file: Path, push_to_trello: bool = True,
                                 index_to_rag: bool = True) -> Dict:
        """
        Complete intelligence pipeline for a VTT summary

        Args:
            summary_file: Path to VTT summary markdown
            push_to_trello: Create Trello cards for action items
            index_to_rag: Index summary in meeting RAG

        Returns:
            Complete pipeline results
        """
        summary_id = summary_file.stem
        logger.info(f"\n{'='*60}")
        logger.info(f"🚀 VTT Intelligence Pipeline: {summary_file.name}")
        logger.info(f"{'='*60}\n")

        # Check if already processed
        if summary_id in self.state["processed_summaries"]:
            logger.info(f"⏭️  Already processed: {summary_file.name}")
            return {"status": "skipped", "reason": "already_processed"}

        results = {
            "summary_file": str(summary_file),
            "timestamp": Path(summary_file).stat().st_mtime,
            "steps": {}
        }

        # Step 1: Extract intelligence
        logger.info("📊 Step 1: Extracting intelligence...")
        try:
            intelligence_results = self.intelligence.process_summary(summary_file)
            results["steps"]["intelligence"] = {
                "status": "success",
                "action_items": len(intelligence_results["action_items"]),
                "decisions": len(intelligence_results["decisions"]),
                "contacts": len(intelligence_results["contacts"])
            }
            logger.info(f"   ✅ Extracted: {len(intelligence_results['action_items'])} actions, "
                       f"{len(intelligence_results['decisions'])} decisions")
        except Exception as e:
            logger.error(f"   ❌ Intelligence extraction failed: {e}")
            results["steps"]["intelligence"] = {"status": "error", "error": str(e)}
            return results

        # Step 2: Push to Trello
        if push_to_trello:
            logger.info(f"\n📌 Step 2: Creating Trello cards for {self.owner}...")
            try:
                if not self.trello_board:
                    logger.warning("   ⚠️  No Trello board configured, skipping")
                    results["steps"]["trello"] = {"status": "skipped", "reason": "no_board"}
                else:
                    trello_results = self.trello_integration.create_cards_for_owner(
                        owner=self.owner,
                        board_id=self.trello_board
                    )
                    results["steps"]["trello"] = {
                        "status": "success",
                        "created": trello_results["created"],
                        "skipped": trello_results["skipped"]
                    }
                    logger.info(f"   ✅ Created {trello_results['created']} cards, "
                               f"skipped {trello_results['skipped']} duplicates")
            except Exception as e:
                logger.error(f"   ❌ Trello integration failed: {e}")
                results["steps"]["trello"] = {"status": "error", "error": str(e)}

        # Step 3: Index to RAG
        if index_to_rag:
            logger.info(f"\n🔍 Step 3: Indexing to Meeting RAG...")
            try:
                rag_results = self.rag_integration.index_summary(summary_file)
                results["steps"]["rag"] = {
                    "status": rag_results["status"],
                    "doc_id": rag_results.get("doc_id")
                }
                logger.info(f"   ✅ {rag_results['status'].upper()}")
            except Exception as e:
                logger.error(f"   ❌ RAG indexing failed: {e}")
                results["steps"]["rag"] = {"status": "error", "error": str(e)}

        # Mark as processed
        self.state["processed_summaries"][summary_id] = results
        self._save_state()

        logger.info(f"\n{'='*60}")
        logger.info(f"✅ Pipeline Complete: {summary_file.name}")
        logger.info(f"{'='*60}\n")

        return results

    def process_all_unprocessed(self, summaries_dir: Optional[Path] = None) -> Dict:
        """
        Process all unprocessed VTT summaries

        Args:
            summaries_dir: Directory containing summaries (default: maia data dir)

        Returns:
            Batch processing results
        """
        if not summaries_dir:
            summaries_dir = MAIA_ROOT / "claude" / "data" / "transcript_summaries"

        summary_files = sorted(summaries_dir.glob("*.md"), key=lambda p: p.stat().st_mtime, reverse=True)

        logger.info(f"\n📁 Found {len(summary_files)} summary files")

        batch_results = {"processed": 0, "skipped": 0, "errors": 0, "details": []}

        for summary_file in summary_files:
            try:
                result = self.process_summary_complete(summary_file)

                if result.get("status") == "skipped":
                    batch_results["skipped"] += 1
                else:
                    batch_results["processed"] += 1

                batch_results["details"].append(result)

            except Exception as e:
                logger.error(f"❌ Failed to process {summary_file.name}: {e}")
                batch_results["errors"] += 1

        return batch_results

    def get_daily_briefing_data(self) -> Dict:
        """Export data for daily briefing integration"""
        briefing_data = self.intelligence.export_for_daily_briefing()

        # Add recent actions for owner
        owner_actions = self.intelligence.get_pending_actions_for_owner(self.owner)

        briefing_data["your_action_items"] = [
            {
                "action": a["action"],
                "deadline": a["deadline"],
                "from_meeting": "recent VTT"
            }
            for a in owner_actions[:5]  # Top 5
        ]

        return briefing_data


def main():
    """CLI interface"""
    import argparse

    parser = argparse.ArgumentParser(description="VTT Intelligence Pipeline")
    parser.add_argument("command", choices=["process", "process-all", "briefing-data"],
                       help="Command to execute")
    parser.add_argument("--file", help="Summary file to process")
    parser.add_argument("--owner", default="Naythan", help="Owner name")
    parser.add_argument("--board", help="Trello board ID")
    parser.add_argument("--no-trello", action="store_true", help="Skip Trello integration")
    parser.add_argument("--no-rag", action="store_true", help="Skip RAG indexing")

    args = parser.parse_args()

    pipeline = VTTIntelligencePipeline(owner=args.owner, trello_board=args.board)

    if args.command == "process":
        if not args.file:
            print("❌ Error: --file required")
            sys.exit(1)

        summary_file = Path(args.file)
        if not summary_file.exists():
            print(f"❌ Error: File not found: {summary_file}")
            sys.exit(1)

        results = pipeline.process_summary_complete(
            summary_file,
            push_to_trello=not args.no_trello,
            index_to_rag=not args.no_rag
        )

        print("\n📊 Pipeline Results:")
        print(json.dumps(results, indent=2))

    elif args.command == "process-all":
        print("\n🚀 Processing all unprocessed VTT summaries...")
        results = pipeline.process_all_unprocessed()

        print(f"\n✅ Batch Processing Complete:")
        print(f"   • Processed: {results['processed']}")
        print(f"   • Skipped: {results['skipped']}")
        print(f"   • Errors: {results['errors']}")

    elif args.command == "briefing-data":
        briefing_data = pipeline.get_daily_briefing_data()
        print("\n📊 Daily Briefing Data:")
        print(json.dumps(briefing_data, indent=2))


if __name__ == "__main__":
    main()
